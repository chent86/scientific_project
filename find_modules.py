from tools import node, node_helper


class find_models:
    def __init__(self, helper: node_helper, r1 = True):
        self.helper = helper
        self.level = dict()  # name : (level, node)
        self.connection_list = dict()  # name : set((name, AEG, node))  因为步骤中只是为了找到level最大的值, 可以不必排序
        self.cur_level = 1
        self.result = set()  # name 已经得到的model的root的name
        self.both_AEG = set()  # name 有两种AEG值的节点名称
        self.LCC_set = set()
        self.LCC_num = 1  # 为LCC阶段新增的门
        self.sdag = dict()  # { root_name : (output, printed_set) } printed_set用于保证在一个module中不重复定义
        self.module_var_index_map = dict()
        self.module_index_var_map = dict()
        self.module_dict = dict()  # { name : module_name } 不替换原有节点名称的代替品
        self.module_dict["r1"] = "m0"
        self.r1 = r1  # False: 以门作为模块  True: 生成新模块

    def init_level(self, cur_node: node):  # 使用了DFS，不与论文步骤完全一致
        if not cur_node.children:
            return
        for child in cur_node.children:
            self.init_level(child)
        self.level[cur_node.name] = (self.cur_level, cur_node)
        self.cur_level += 1

    def init_connection_list(self, cur_node: node):
        for child in cur_node.children:
            if cur_node.gate_type == "or" and cur_node.sign[child.name] == 0:  # 1, 3 对应论文AEG = 1
                AEG = 1
            elif cur_node.gate_type == "and" and cur_node.sign[child.name] == 1:
                AEG = 3
            elif cur_node.gate_type == "or" and cur_node.sign[child.name] == 1:  # 2, 4 对应论文AEG = -1
                AEG = 2
            elif cur_node.gate_type == "and" and cur_node.sign[child.name] == 0:
                AEG = 4
            if child.name in self.connection_list:
                for _, _AEG, _ in self.connection_list[child.name]:  # 判断connection_list中是否有两种AEG
                    if _AEG % 2 != AEG % 2:  # 属于论文中描述的同一类
                        self.both_AEG.add(child.name)
                        break
                if cur_node.name not in {name for (name, _, _) in self.connection_list[child.name]}:
                    self.connection_list[child.name].add((cur_node.name, AEG, cur_node))
            else:
                self.connection_list[child.name] = {(cur_node.name, AEG, cur_node)}
            if child.children:
                self.init_connection_list(child)
            
    def check(self):
        self.PC_check()
        # print(self.module_dict)

    def PC_check(self):
        for node_name in self.level:
            (_, cur_node) = self.level.get(node_name)
            flag = True
            for child in cur_node.children:
                if self.get_top_level({name for (name, _, _) in self.connection_list[child.name]}) != cur_node.name:
                    flag = False
                    break
            if flag:
                self.CC_check(cur_node)

    def get_top_level(self, level_set):
        top = None
        for i in level_set:
            if not top:
                top = i
            elif self.level[i][0] > self.level[top][0]:
                top = i
        return top

    def CC_check(self, cur_node):
        expand_set = set()  # 当前model包括的节点
        connection_set = set()  # 所有节点的connection_list包含的节点
        basic_or_top = dict()  # expand中的basic和module top, 用于LCC阶段 name
        expand_set.add(cur_node.name)
        self.CC_helper(expand_set, connection_set, cur_node, basic_or_top)
        flag = True
        for i in connection_set:
            if i not in expand_set:
                flag = False
                break
        if flag:
            self.LCC_check(cur_node, basic_or_top)

    def CC_helper(self, expand_set, connection_set, cur_node, basic_or_top):
        for child in cur_node.children:
            expand_set.add(child.name)
            for i in self.connection_list[child.name]:
                connection_set.add(i[0])
            if not child.children or child.name in self.result:
                if child.name not in self.both_AEG:  # 排除有两种AEG的节点
                    basic_or_top[child.name] = cur_node.gate_type
            else:
                self.CC_helper(expand_set, connection_set, child, basic_or_top)

    def LCC_check(self, cur_node, basic_or_top):
        if cur_node.name not in self.module_dict:
            self.module_dict[cur_node.name] = "m" + str(self.LCC_num)
            self.LCC_num += 1
        self.result.add(cur_node.name)
        if not self.r1:
            return
        obtained_set = [[name] for name in basic_or_top]  # TODO 在同一个module的扩展中，是否会出现相同的节点？
        cur = 0
        while cur < len(obtained_set) - 1:  # 获取具有相同connection_list的节点
            if not obtained_set[cur]:
                cur += 1
                continue
            for i in range(cur + 1, len(obtained_set)):
                if not obtained_set[i]:
                    continue
                # 只比较connection_list，不比较AEG
                if {name for (name, _, _) in self.connection_list[obtained_set[cur][0]]} == \
                   {name for (name, _, _) in self.connection_list[obtained_set[i][0]]}:
                    obtained_set[cur].append(obtained_set[i][0])
                    obtained_set[i].remove(obtained_set[i][0])
            cur += 1
        for s in obtained_set:
            if len(s) > 1:
                for _, first_AEG, first_gate_node in self.connection_list[s[0]]:
                    break
                node_exist = False  # 一个完整结点是其他结点的一部分
                for _, m_AEG, gate_node in self.connection_list[s[0]]:
                    if len(gate_node.children) == len(s):
                        node_exist = True
                        module_node = gate_node
                        break
                if not node_exist:
                    new_node = self.helper.create_node("m" + str(self.LCC_num))  # 集合共享一个module
                    self.LCC_num += 1
                    new_node.gate_type = first_gate_node.gate_type
                    for name in s:
                        child = self.helper.create_node(name)  # 返回的是原来的节点
                        self.helper.add_child(new_node, child, first_gate_node.sign[name])
                    for _, cur_AEG, gate_node in self.connection_list[s[0]]:
                        for name in s:
                            child = self.helper.create_node(name)
                            self.helper.delete_child(gate_node, child)
                        if cur_AEG == first_AEG:
                            self.helper.add_child(gate_node, new_node, 0)
                        else:
                            self.helper.add_child(gate_node, new_node, 1)
                    self.result.add(new_node.name)
                else:
                    for _, cur_AEG, gate_node in self.connection_list[s[0]]:
                        if len(gate_node.children) > len(module_node.children):
                            for name in s:
                                child = self.helper.create_node(name)
                                self.helper.delete_child(gate_node, child)
                            if cur_AEG == first_AEG:
                                self.helper.add_child(gate_node, module_node, 0)
                            else:
                                self.helper.add_child(gate_node, module_node, 1)
                        elif module_node != gate_node and len(module_node.children) == len(gate_node.children):
                            for _, _, parent in self.connection_list[gate_node.name]:
                                self.helper.delete_child(parent, gate_node)
                                if cur_AEG == m_AEG:
                                    self.helper.add_child(parent, module_node, 0)
                                else:
                                    self.helper.add_child(parent, module_node, 1)
                    self.result.add(module_node.name)
                    if module_node.name not in self.module_dict:
                        self.module_dict[module_node.name] = "m" + str(self.LCC_num)
                        self.LCC_num += 1

#  { m1 : (output, printed_set) }
    def get_sdag(self, cur_node: node, cur_root_name):
        if cur_node.name == cur_root_name:
            if cur_root_name in self.sdag:
                return
            else:
                self.sdag[cur_root_name] = ["", set()]
        if not cur_node.children:
            return
        if cur_node.name in self.sdag[cur_root_name][1]:  # 当前模块内的重复子模块
            return
        line = ""
        if cur_node.name == cur_root_name:
            line += "r1"
        else:
            line += cur_node.name
        line += " := ("
        operator = self.helper.inv_operator_tag[cur_node.gate_type]
        for i in cur_node.children:
            if cur_node.sign[i.name] == 1:
                line += "-"
            if i.name in self.module_dict:
                line += self.module_dict[i.name] + " " + operator + " "
            else:
                line += i.name + " " + operator + " "
        line = line[:len(line) - 3] + ");"
        self.sdag[cur_root_name][0] += line + "\n"
        self.sdag[cur_root_name][1].add(cur_node.name)
        for i in cur_node.children:
            if i.name not in self.result:  # 不是一个新的模块
                self.get_sdag(i, cur_root_name)
            else:
                self.get_sdag(i, i.name)

    def get_real_name(self, name):
        if name in self.module_dict:
            return self.module_dict[name]
        return name

    def output_sdag(self, output_file_dir, file_name):
        for key in self.sdag:
            if key == "r1":
                path = file_name + "_m0.sdag"
            else:
                path = file_name + "_" + self.get_real_name(key) + ".sdag"
            open(output_file_dir + path, "w").write(self.sdag.get(key)[0])

    def get_cnf(self, output_file_dir, file_name, SIMPLE_OUTPUT):
        for node_name in self.result:
            cnf_result = ""
            cur_node = self.helper.create_node(node_name)
            divide_set = {"not-child": set(), "is-child": set()}
            self.divide_node(cur_node, divide_set)
            num_dict = {}  # name : num
            inv_num_dict = {}  # num : name
            i = 1
            for name in divide_set["is-child"]:
                real_name = self.get_real_name(name)
                num_dict[real_name] = i
                inv_num_dict[i] = real_name
                i += 1
            real_module_name = self.get_real_name(cur_node.name)
            num_dict[real_module_name] = i
            inv_num_dict[i] = real_module_name
            # num_dict["r1"] = i
            # inv_num_dict[i] = "r1"
            i += 1
            for name in divide_set["not-child"]:
                real_name = self.get_real_name(name)
                num_dict[real_name] = i
                inv_num_dict[i] = real_name
                i += 1
            self.module_var_index_map[real_module_name] = num_dict
            self.module_index_var_map[real_module_name] = inv_num_dict
            divide_set["not-child"].add(cur_node.name)
            total_node_num = len(divide_set["not-child"]) + len(divide_set["is-child"])
            total_line_num = 1
            line_scope = dict()  # {num : [from, to]}
            line = ""
            for name in divide_set["not-child"]:
                line_scope[num_dict[self.get_real_name(name)]] = [total_line_num]
                cur_node = self.helper.create_node(name)
                if cur_node.gate_type == "and":
                    for child in cur_node.children:
                        line += "-" + str(num_dict[self.get_real_name(cur_node.name)]) + " "
                        if cur_node.sign[child.name]:
                            line += "-"
                        line += str(num_dict[self.get_real_name(child.name)]) + " 0\n"
                        total_line_num += 1
                    line += str(num_dict[self.get_real_name(cur_node.name)]) + " "
                    for child in cur_node.children:
                        if cur_node.sign[child.name] == 1:
                            line += str(num_dict[self.get_real_name(child.name)]) + " "
                        else:
                            line += "-" + str(num_dict[self.get_real_name(child.name)]) + " "
                    line += "0\n"
                    total_line_num += 1
                else:
                    for child in cur_node.children:
                        line += str(num_dict[self.get_real_name(cur_node.name)]) + " "
                        if cur_node.sign[child.name] == 1:
                            line += str(num_dict[self.get_real_name(child.name)]) + " 0\n"
                        else:
                            line += "-" + str(num_dict[self.get_real_name(child.name)]) + " 0\n"
                        total_line_num += 1
                    line += "-" + str(num_dict[self.get_real_name(cur_node.name)]) + " "
                    for child in cur_node.children:
                        if cur_node.sign[child.name]:
                            line += "-"
                        line += str(num_dict[self.get_real_name(child.name)]) + " "
                    line += "0\n"
                    total_line_num += 1
                line_scope[num_dict[self.get_real_name(name)]].append(total_line_num - 1)

            if SIMPLE_OUTPUT:
                child_num = len(divide_set["is-child"])
                cnf_result += "c n orig vars " + str(child_num) + "\n"

            if not SIMPLE_OUTPUT:
                for name in num_dict:
                    if name == real_module_name:
                        cnf_result += "c " + str(num_dict.get(name)) + " = r1\n"
                    else:
                        cnf_result += "c " + str(num_dict.get(name)) + " = " + name + "\n"
                cnf_result += "c\n"
                cnf_result += "n " + str(len(divide_set["is-child"])) + "\n"
                cnf_result += "c\n"
                for key in line_scope:
                    cnf_result += "b " + str(key) + " " + str(line_scope.get(key)[0]) + " " + str(line_scope.get(key)[1]) + "\n"
                cnf_result += "c\n"

            cnf_result += "p cnf " + str(total_node_num) + " " + str(total_line_num) + "\n"
            p_cnf_result = cnf_result + str(num_dict[self.get_real_name(node_name)]) + " 0\n"
            n_cnf_result = cnf_result + "-" + str(num_dict[self.get_real_name(node_name)]) + " 0\n"
            cnf_result = ""
            cnf_result += line
            if node_name == "r1":
                p_path = file_name + "_m0-p.cnf"
                n_path = file_name + "_m0-n.cnf"
            else:
                p_path = file_name + "_" + self.get_real_name(node_name) + "-p.cnf"
                n_path = file_name + "_" + self.get_real_name(node_name) + "-n.cnf"
            p_cnf_result += cnf_result
            n_cnf_result += cnf_result
            open(output_file_dir + p_path, "w").write(p_cnf_result)
            open(output_file_dir + n_path, "w").write(n_cnf_result)

    def divide_node(self, cur_node, divide_set):
        for child in cur_node.children:
            if not child.children or child.name in self.result:
                divide_set["is-child"].add(child.name)
            else:
                divide_set["not-child"].add(child.name)
                self.divide_node(child, divide_set)

    def check_module_helper(self):
        node_list = []
        key_list = []
        for key, node_dict in self.module_var_index_map.items():
            key_list.append(key)
            node_list.append({name for name in node_dict})
        for i in range(0, len(node_list)):
            for j in range(0, len(node_list)):
                if j != i:
                    if len(node_list[i] & node_list[j]) != 1:
                        print("\nnot modularized!!!")
                        # sys.exit()
                        return False
        return True


class handler:
    def __init__(self, input_file_dir, output_file_dir, file_name, r0 = True, r1 = True, SIMPLE_OUTPUT = False):
        self.gate_num = 0
        self.basic_num = 0
        self.origin_basic_event_num = 0
        self.origin_gate_event_num = 0
        self.simplify_time = 0
        self.module_time = 0
        self.coherent_map = dict()  # node_name: bool
        self.root_map = dict()  # module_name: root_index
        h = node_helper()
        h.parser(input_file_dir + file_name + "/" + file_name + ".sdag")
        self.f = find_models(h, r1)
        if r0:
            self.f.init_level(h.root_node)
            self.f.init_connection_list(h.root_node)
            self.f.check()
        else:
            self.f.result.add("r1")
        # print(self.f.result)
        # h.format(h.root_node)
        self.f.get_sdag(h.root_node, h.root_node.name)
        self.f.output_sdag(output_file_dir + file_name + "/", file_name)
        self.f.get_cnf(output_file_dir + file_name + "/", file_name, SIMPLE_OUTPUT)
        self.get_gate_and_basic_num()
        self.check_coherent()

    def get_gate_and_basic_num(self):
        for n in self.f.helper.node_dict.values():
            if n.children:
                self.gate_num += 1
            else:
                self.basic_num += 1

    def check_coherent(self):
        for name in self.f.result:
            root_node = self.f.helper.node_dict.get(name)
            leaves = dict()
            # self.coherent_map[self.f.get_real_name(name)] = self.coherent_helper(root_node, leaves)
            self.coherent_map[self.f.get_real_name(name)] = self.tmp_coherent_check(root_node)

    # def coherent_helper(self, cur_node, leaves):
    #     for child in cur_node.children:
    #         if not child.children or child.name in self.f.result:
    #             if child.name in leaves:
    #                 if leaves.get(child.name) != cur_node.sign[child.name]:
    #                     return False
    #             else:
    #                 leaves[child.name] = cur_node.sign[child.name]
    #         else:
    #             if not self.coherent_helper(child, leaves):
    #                 return False
    #     return True

    def tmp_coherent_check(self, cur_node):
        for sign in cur_node.sign.values():
            if sign:
                return False
        for child in cur_node.children:
            if child.children and child.name not in self.f.result:
                result = self.tmp_coherent_check(child)
                if not result:
                    return False
        return True

    def data(self):
        # 将map中的根全部换成r1
        for key, map_dict in self.f.module_var_index_map.items():
            for node_name, index in map_dict.items():
                if node_name == key:
                    map_dict["r1"] = index
                    self.root_map[key] = index
                    map_dict.pop(node_name)
                    break
        for key, map_dict in self.f.module_index_var_map.items():
            for index, node_name in map_dict.items():
                if node_name == key:
                    map_dict[index] = "r1"
                    break
        # print(self.f.helper.gate_num)
        return {
            "origin_basic_event_num": self.origin_basic_event_num,
            "origin_gate_evnet_num": self.origin_gate_event_num,
            "basic_event_num": self.basic_num,
            "gate_event_num": self.gate_num,
            "coherent_map": self.coherent_map,
            "modules_num": len(self.f.result),
            "module_var_index_map": self.f.module_var_index_map,
            "module_index_var_map": self.f.module_index_var_map,
            "modularized": self.f.check_module_helper(),
            "root_map": self.root_map,
            "simplify_time": self.simplify_time,
            "module_time": self.module_time
        }

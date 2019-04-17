from tools import node, node_helper


class find_models:
    def __init__(self, helper: node_helper):
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
        self.basic_event_num = 0
        self.gate_event_num = 0

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

    def PC_check(self):
        for node_name in self.level:
            (_, cur_node) = self.level.get(node_name)
            flag = True
            for child in cur_node.children:
                if self.get_top_level({name for (name, _, _) in self.connection_list[child.name]}) != cur_node.name:
                    flag = False
                    break
            if flag:
                # print(node_name + " pass PC check")
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
            # print(cur_node.name + " pass CC check")
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
        self.result.add(cur_node.name)
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
                for _, _, gate_node in self.connection_list[s[0]]:
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
                                self.helper.add_child(gate_node, new_node, 0)
                            else:
                                self.helper.add_child(gate_node, new_node, 1)
                    self.result.add(module_node.name)           

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
            line += i.name + " " + operator + " "
        line = line[:len(line) - 3] + ");"
        self.sdag[cur_root_name][0] += line + "\n"
        self.sdag[cur_root_name][1].add(cur_node.name)
        for i in cur_node.children:
            if i.name not in self.result:  # 不是一个新的模块
                self.get_sdag(i, cur_root_name)
            else:
                self.get_sdag(i, i.name)

    def output_sdag(self, output_file_dir, file_name):
        for key in self.sdag:
            if key == "r1":
                path = file_name + "_m0.sdag"
            else:
                path = file_name + "_" + key + ".sdag"
            open(output_file_dir + path, "w").write(self.sdag.get(key)[0])

    def get_cnf(self, output_file_dir, file_name):
        for node_name in self.result:
            cnf_result = ""
            cur_node = self.helper.create_node(node_name)
            divide_set = {"not-child": set(), "is-child": set()}
            self.divide_node(cur_node, divide_set)
            num_dict = {}  # name : num
            inv_num_dict = {}  # num : name
            i = 1
            for name in divide_set["is-child"]:
                num_dict[name] = i
                inv_num_dict[i] = name
                i += 1
            num_dict[cur_node.name] = i
            inv_num_dict[i] = cur_node.name
            i += 1
            for name in divide_set["not-child"]:
                num_dict[name] = i
                inv_num_dict[i] = name
                i += 1
            self.module_var_index_map[cur_node.name] = num_dict
            self.module_index_var_map[cur_node.name] = inv_num_dict
            divide_set["not-child"].add(cur_node.name)
            total_node_num = len(divide_set["not-child"]) + len(divide_set["is-child"])
            self.basic_event_num = len(divide_set["is-child"])
            self.gate_event_num = len(divide_set["not-child"])
            total_line_num = 1
            line_scope = dict()  # {num : [from, to]}
            line = ""
            for name in divide_set["not-child"]:
                line_scope[num_dict[name]] = [total_line_num]
                cur_node = self.helper.create_node(name)
                if cur_node.gate_type == "and":
                    for child in cur_node.children:
                        line += "-" + str(num_dict[cur_node.name]) + " " + str(num_dict[child.name]) + " 0\n"
                        total_line_num += 1
                    line += str(num_dict[cur_node.name]) + " "
                    for child in cur_node.children:
                        if cur_node.sign[child.name] == 1:
                            line += str(num_dict[child.name]) + " "
                        else:
                            line += "-" + str(num_dict[child.name]) + " "
                    line += "0\n"
                    total_line_num += 1
                else:
                    for child in cur_node.children:
                        line += str(num_dict[cur_node.name]) + " "
                        if cur_node.sign[child.name] == 1:
                            line += str(num_dict[child.name]) + " 0\n"
                        else:
                            line += "-" + str(num_dict[child.name]) + " 0\n"
                        total_line_num += 1
                    line += "-" + str(num_dict[cur_node.name]) + " "
                    for child in cur_node.children:
                        line += str(num_dict[child.name]) + " "
                    line += "0\n"
                    total_line_num += 1
                line_scope[num_dict[name]].append(total_line_num - 1)

            for name in num_dict:
                if name == cur_node.name:
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
            p_cnf_result = cnf_result + str(num_dict[node_name]) + " 0\n"
            n_cnf_result = cnf_result + "-" + str(num_dict[node_name]) + " 0\n"
            cnf_result = ""
            cnf_result += line
            if node_name == "r1":
                p_path = file_name + "_m0-p.cnf"
                n_path = file_name + "_m0-n.cnf"
            else:
                p_path = file_name + "_" + node_name + "-p.cnf"
                n_path = file_name + "_" + node_name + "-n.cnf"
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


class handler:
    def __init__(self, input_file_dir, output_file_dir, file_name):
        h = node_helper()
        h.parser(input_file_dir + file_name + "/" + file_name + ".sdag")
        self.f = find_models(h)
        self.f.init_level(h.root_node)
        self.f.init_connection_list(h.root_node)
        self.f.check()
        # print(self.f.result)
        # h.format(h.root_node)
        self.f.get_sdag(h.root_node, h.root_node.name)
        self.f.output_sdag(output_file_dir + file_name + "/", file_name)
        self.f.get_cnf(output_file_dir + file_name + "/", file_name)

    def data(self):
        return {
            "is_coherent": self.f.helper.check_coherent(),
            "basic_event_num": self.f.basic_event_num,
            "gate_event_num": self.f.gate_event_num,
            "modules_num": len(self.f.result),
            "module_var_index_map": self.f.module_var_index_map,
            "module_index_var_map": self.f.module_index_var_map
        }

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
                    if _AEG%2 != AEG%2:
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
                # for i in s:
                #     print(i, basic_or_top[i], self.connection_list[i])
                self.LCC_set.add(new_node.name)
                    

if __name__ == "__main__":
    h = node_helper()
    h.parser("./data/result/test.sdag")
    f = find_models(h)
    f.init_level(h.root_node)
    f.init_connection_list(h.root_node)
    f.check()
    print(f.result)
    print(f.LCC_set)
    h.format(h.root_node)

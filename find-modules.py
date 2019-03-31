from tools import node, node_helper


class find_models:
    def __init__(self, helper: node_helper):
        self.helper = helper
        self.level = dict()  # name : (level, node)
        self.connection_list = dict()  # name : set((name, AEG))  因为步骤中只是为了找到level最大的值, 可以不必排序
        self.cur_level = 1
        self.result = set()  # name 已经得到的model的root的name
        self.both_AEG = set()  # name 有两种AEG值的节点名称
        self.LCC_set = set()

    def init_level(self, cur_node: node):  # 使用了DFS，不与论文步骤完全一致
        if not cur_node.children:
            return
        for child in cur_node.children:
            self.init_level(child)
        self.level[cur_node.name] = (self.cur_level, cur_node)
        self.cur_level += 1

    def init_connection_list(self, cur_node: node):
        for child in cur_node.children:
            if (cur_node.gate_type == "or" and cur_node.sign[child.name] == 0) or\
                (cur_node.gate_type == "and" and cur_node.sign[child.name] ==1):
                AEG = 1
            else:
                AEG = 0
            if child.name in self.connection_list:
                for name, _AEG in self.connection_list[child.name]:  # 判断connection_list中是否有两种AEG
                    if cur_node.name == name:
                        if _AEG != AEG:
                            self.both_AEG.add(cur_node)
                            break
                if cur_node.name not in {name for (name,_) in self.connection_list[child.name]}:
                    self.connection_list[child.name].add((cur_node.name, AEG))
            else:
                self.connection_list[child.name] = {(cur_node.name, AEG)}
            if child.children:
                self.init_connection_list(child)
            
    def check(self):
        self.PC_check()

    def PC_check(self):
        for node_name in self.level:
            (_, cur_node) = self.level.get(node_name)
            flag = True
            for child in cur_node.children:
                if self.get_top_level({name for (name, AEG) in self.connection_list[child.name]}) != cur_node.name:
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
        while cur < len(obtained_set)-1:  # 获取具有相同connection_list的节点
            if not obtained_set[cur]:
                cur += 1
                continue
            for i in range(cur+1, len(obtained_set)):
                if not obtained_set[i]:
                    continue
                # 只比较connection_list，不比较AEG
                if {name for (name, AEG) in self.connection_list[obtained_set[cur][0]]} == \
                    {name for (name, AEG) in self.connection_list[obtained_set[i][0]]}:
                    obtained_set[cur].append(obtained_set[i][0])
                    obtained_set[i].remove(obtained_set[i][0])
            cur += 1
        for s in obtained_set:
            if len(s) > 1:
                for i in s:
                    print(i, basic_or_top[i], self.connection_list[i])
                print("==================")
                # if len(self.connection_list[s[0]]) != 1:
                #     raise Exception("connection_list length more than 1 !", self.connection_list[s[0]])
                # else:
                while self.connection_list[s[0]]:
                    name, _ = self.connection_list[s[0]].pop()
                    self.LCC_set.add(name)
                    # self.result.add(name)
                    

if __name__ == "__main__":
    h = node_helper()
    h.parser("./data/result/test.sdag")
    f = find_models(h)
    f.init_level(h.root_node)
    f.init_connection_list(h.root_node)
    f.check()
    print(f.result)
    print(f.LCC_set)

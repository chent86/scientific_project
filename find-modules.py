from tools import node, node_helper


class find_models:
    def __init__(self, helper: node_helper):
        self.helper = helper
        self.level = dict()  # name : (level, node)
        self.connection_list = dict()  # name : set(name)  因为步骤中只是为了找到level最大的值, 可以不必排序
        self.cur_level = 1
        self.result = set()  # name 已经得到的model的root的name

    def init_level(self, cur_node: node):  # 使用了DFS，不与论文步骤完全一致
        if not cur_node.children:
            return
        for child in cur_node.children:
            self.init_level(child)
        self.level[cur_node.name] = (self.cur_level, cur_node)
        self.cur_level += 1

    def init_connection_list(self, cur_node: node):
        for child in cur_node.children:
            if child.name in self.connection_list:
                self.connection_list[child.name].add(cur_node.name)
            else:
                self.connection_list[child.name] = {cur_node.name}
            if child.children:
                self.init_connection_list(child)
            
    def check(self):
        self.PC_check()

    def PC_check(self):
        for node_name in self.level:
            (_, cur_node) = self.level.get(node_name)
            flag = True
            for child in cur_node.children:
                if self.get_top_level(self.connection_list[child.name]) != cur_node.name:
                    flag = False
                    break
            if flag:
                print(node_name + " pass PC check")
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
        expand_set.add(cur_node.name)
        self.CC_helper(expand_set, connection_set, cur_node)
        flag = True
        for i in connection_set:
            if i not in expand_set:
                flag = False
                break
        if flag:
            print(cur_node.name + " pass CC check")
            self.LCC_check(cur_node)

    def CC_helper(self, expand_set, connection_set, cur_node):
        if not cur_node.children or cur_node.name in self.result:
            return
        for child in cur_node.children:
            expand_set.add(child.name)
            for i in self.connection_list[child.name]:
                connection_set.add(i)

    def LCC_check(self, cur_node):
        self.result.add(cur_node.name)


if __name__ == "__main__":
    h = node_helper()
    h.parser("./data/result/test.sdag")
    f = find_models(h)
    f.init_level(h.root_node)
    f.init_connection_list(h.root_node)
    f.check()
    print(f.result)

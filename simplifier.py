from tools import node, node_helper, inv_operator_tag


class simplifier:
    def __init__(self, helper: node_helper):
        self.result = ""
        self.helper = helper

    def simplify(self, cur_node):
        visited_set = set()
        self.simplify_helper(cur_node, visited_set)

    def simplify_helper(self, cur_node, visited_set):
        if len(cur_node.children) == 0:
            return
        children_list = [child for child in cur_node.children]  # 避免迭代器失效
        if len(children_list) == 1:
            expire_child = cur_node.children[0]
            self.helper.delete_child(cur_node, expire_child)
            cur_node.name = expire_child.name
            cur_node.gate_type = expire_child.gate_type
            cur_node.children = expire_child.children
            return
        i = 0
        while i < len(children_list):
            if cur_node.gate_type == children_list[i].gate_type:
                for j in children_list[i].children:
                    self.helper.add_child(cur_node, j, children_list[i].sign[j.name])
                self.helper.delete_child(cur_node, children_list[i])
                i -= 1
            else:
                self.simplify_helper(children_list[i], visited_set)
                if children_list[i].children:  # 从最倒数第二层子树开始考虑, 自底向上合并等效的节点
                    flag = True
                    for visited_node in visited_set:
                        if visited_node.name == children_list[i].name:
                            flag = False
                            break
                        if visited_node.gate_type == children_list[i].gate_type:
                            if visited_node.sign == children_list[i].sign:
                                sign = cur_node.sign.get(children_list[i].name)
                                cur_node.sign.pop(children_list[i].name)
                                cur_node.sign[visited_node.name] = sign
                                cur_node.children.remove(children_list[i])
                                cur_node.children.add(visited_node)
                                flag = False
                                break
                    if flag:
                        visited_set.add(children_list[i])
            i += 1
        if len(cur_node.children) == 1:
            for expire_child in cur_node.children:
                break
            self.helper.delete_child(cur_node, expire_child)
            cur_node.gate_type = expire_child.gate_type
            cur_node.children = expire_child.children
            cur_node.sign = expire_child.sign

    def format(self, cur_node: node):
        if not cur_node.children:
            return
        line = ""
        line += cur_node.name
        line += " := ("
        operator = inv_operator_tag[cur_node.gate_type]
        for i in cur_node.children:
            if cur_node.sign[i.name] == 1:
                line += "-"
            line += i.name + " " + operator + " "
        line = line[:len(line) - 3] + ");"
        print(line)
        self.result += line + "\n"
        for i in cur_node.children:
            self.format(i)


if __name__ == "__main__":
    h = node_helper()
    h.parser("./data/result/test.dag")
    s = simplifier(h)
    s.simplify(h.root_node)
    s.format(h.root_node)
    sdag = open("./data/result/test.sdag", "w")
    sdag.write(s.result)

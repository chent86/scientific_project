from tools import node, node_helper, inv_operator_tag


class simplifier:
    def __init__(self, helper: node_helper):
        self.result = ""
        self.helper = helper

    def simplify(self, cur_node):
        if len(cur_node.children) == 0:
            return
        if len(cur_node.children) == 1:
            expire_child = cur_node.children[0]
            self.helper.delete_child(cur_node, expire_child)
            cur_node.name = expire_child.name
            cur_node.gate_type = expire_child.gate_type
            cur_node.children = expire_child.children
            return
        i = 0
        while i < len(cur_node.children):
            if cur_node.gate_type == cur_node.children[i].gate_type:
                for j in cur_node.children[i].children:
                    self.helper.add_child(cur_node, j, cur_node.children[i].sign[j.name])
                self.helper.delete_child(cur_node, cur_node.children[i])
                i -= 1  # 迭代器失效
            else:
                self.simplify(cur_node.children[i])
            i += 1

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

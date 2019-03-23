# 将非考虑为不同的event
# todo: 支持多元异或，对于n元异或，分为n-1个门
# todo: 支持atleast, 使用递归

class simplifier:
    class node:
        name = ""
        gate_type = ""
        children = []
        def __init__ (self, name, gate_type = "basic"):
            self.name = name
            self.gate_type = gate_type
            self.children = [] # 不再此self就是静态变量

    node_list = []
    root_node = node("r1")
    operator_tag = {"|":"or", "&":"and", "#":"xor", "-":"not"}

    @staticmethod
    def create_node(name):
        for i in simplifier.node_list:
            if i.name == name:
                return i
        new_node = simplifier.node(name)
        simplifier.node_list.append(new_node)
        if name == "r1":
            simplifier.root_node = new_node
        return new_node
    @staticmethod
    def delete_child(parent_node, child_node):
        parent_node.children.remove(child_node) # 删除父指向子的指针

    @staticmethod
    def update_gate(cur_node, gate_type):
        cur_node.gate_type = gate_type

    @staticmethod
    def add_child(parent_node, child_node):
        already = False
        for i in parent_node.children:
            if i.name == child_node.name:
                already = True
                break
        if not already:
            parent_node.children.append(child_node)

    @staticmethod
    def parser(file_name):
        raw = open(file_name, "r")
        not_in_one_line = 0
        last_line = ""
        is_annotation = 0 # 一片注释
        xo = 0 # 为xor新增加的门
        for line in raw:
            # 处理空行
            if len(line) == 1:
                continue
            # 处理注释
            if line[0] == "/":
                if line[len(line)-2] != "/":
                    is_annotation = 1
                continue
            if is_annotation == 1:
                if line[len(line)-2] != "/":
                    continue
                else:
                    is_annotation = 0
                    continue
            # 处理未在一行的情况
            if line[len(line)-2] != ";" and line[len(line)-1] != ";": # 最后一个字符可能是\n
                last_line += line
                not_in_one_line = 1
                continue
            if not_in_one_line == 1:
                not_in_one_line = 0
                line = last_line+line
                last_line = ""
            length = len(line)
            root = ""
            operator = "&"
            cur = ""
            i = 0
            flag = 0 # 是否是atleast
            num = ""
            cur_list = []
            # 读取门的名称
            for i in range(0, length-1):
                if line[i] == " " or line[i] == ":":
                    break
                root += line[i]
            gate_node = simplifier.create_node(root)
            while i < length-1:
                if line[i] == "=":
                    i = i+1
                    while line[i] == "(" or line[i] == " ":
                        i = i+1
                    # 处理 1、a := b 2、a := (b&c) 3、 a := @(3,[b,c])
                    if line[i] == "@":
                        i = i+1
                        while line[i] == "(" or line[i] == " ":
                            i = i+1
                        flag = 1
                    break
                i = i+1
            if flag == 0: # 不是atleast的情况
                while i < length:
                    if line[i] == "&" or line[i] == "|" or line[i] == "#":
                        operator = line[i]
                        cur_list.append(simplifier.create_node(cur))
                        cur = ""
                        i = i+1
                        continue
                    if line[i] == ")" or line[i] == ";":
                        cur_list.append(simplifier.create_node(cur))
                        cur = ""
                        break
                    if line[i] != " ":
                        cur += line[i]
                    i = i+1
                gate_node.gate_type = simplifier.operator_tag[operator]
                for i in cur_list:
                    simplifier.create_node(i)
                    simplifier.add_child(gate_node, i)       
        raw.close()
    @staticmethod
    def simplify(cur_node):
        if len(cur_node.children) == 0:
            return
        if len(cur_node.children) == 1:
            expire_child = cur_node.children[0]
            simplifier.delete_child(cur_node, expire_child)
            cur_node.name = expire_child.name
            cur_node.children = expire_child.children
            return
        i = 0
        while i < len(cur_node.children):
            if cur_node.gate_type == cur_node.children[i].gate_type:
                for j in cur_node.children[i].children:
                    cur_node.children.append(j)
                simplifier.delete_child(cur_node, cur_node.children[i])
                i -= 1 #迭代器失效
            else:
                simplifier.simplify(cur_node.children[i])
            i += 1
    @staticmethod
    def check(cur_node):
        print("@", cur_node.name)
        for i in cur_node.children:
            print(i.name)
        for i in cur_node.children:
            simplifier.check(i)

if __name__ == "__main__":
    simplifier.parser("./motor2.dag")
    simplifier.simplify(simplifier.root_node)
    simplifier.check(simplifier.root_node)

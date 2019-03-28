# 非没有进行判断，将其作为普通字符(由于节点要共享孩子信息，所以非不能存储在节点中，因为有的非，有的不是非)
# 解决方案可能为：将children设计为二元组，第一项代表符号


class simplifier:
    class node:
        def __init__(self, name, gate_type = "basic"):
            self.name = name
            self.gate_type = gate_type
            self.children = []  # 不再此self就是静态变量

    node_list = []
    root_node = node("r1")
    operator_tag = {"|": "or", "&": "and", "#": "xor", "-": "not"}
    inv_operator_tag = {"or": "|", "and": "&", "xor": "#", "not": "-"}
    xor_num = 0  # 为xor新增的门
    at_least_num = 0  # 为at_least新增的门
    result = ""
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
        parent_node.children.remove(child_node)  # 删除父指向子的指针

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
        is_annotation = 0  # 一片注释
        for line in raw:
            # 处理空行
            if len(line) == 1:
                continue
            # 处理注释
            if line[0] == "/":
                if line[len(line) - 2] != "/":
                    is_annotation = 1
                continue
            if is_annotation == 1:
                if line[len(line) - 2] != "/":
                    continue
                else:
                    is_annotation = 0
                    continue
            # 处理未在一行的情况
            if line[len(line) - 2] != ";" and line[len(line) - 1] != ";":  # 最后一个字符可能是\n
                last_line += line
                not_in_one_line = 1
                continue
            if not_in_one_line == 1:
                not_in_one_line = 0
                line = last_line + line
                last_line = ""
            length = len(line)
            root = ""
            operator = "&"
            cur = ""
            i = 0
            flag = 0  # 是否是atleast
            cur_list = []
            # 读取门的名称
            for i in range(0, length - 1):
                if line[i] == " " or line[i] == ":":
                    break
                root += line[i]
            gate_node = simplifier.create_node(root)
            while i < length - 1:
                if line[i] == "=":
                    i = i + 1
                    while line[i] == "(" or line[i] == " ":
                        i = i + 1
                    # 处理 1、a := b 2、a := (b&c) 3、 a := @(3,[b,c])
                    if line[i] == "@":
                        i = i + 1
                        while line[i] == "(" or line[i] == " ":
                            i = i + 1
                        flag = 1
                    break
                i = i + 1
            if flag == 0:  # 不是atleast的情况
                while i < length:
                    if line[i] == "&" or line[i] == "|" or line[i] == "#":
                        operator = line[i]
                        cur_list.append(simplifier.create_node(cur))
                        cur = ""
                        i = i + 1
                        continue
                    if line[i] == ")" or line[i] == ";":
                        cur_list.append(simplifier.create_node(cur))
                        cur = ""
                        break
                    if line[i] != " ":
                        cur += line[i]
                    i = i + 1
                if operator != "#":
                    gate_node.gate_type = simplifier.operator_tag[operator]
                    for i in cur_list:
                        simplifier.add_child(gate_node, i)
                else:  # 处理多元异或
                    gate_node.gate_type = simplifier.operator_tag["|"]
                    xor_root = gate_node
                    while xor_root:
                        first_node = cur_list[0]
                        cur_list = cur_list[1:]
                        xor_root = simplifier.xor_helper(xor_root, first_node, cur_list)
            else:
                count = ""  # atleast中至少几个为真
                gate_node.gate_type = simplifier.operator_tag["|"]
                while i < length:
                    if line[i] == "," or line[i] == " ":
                        break
                    count += line[i]
                    i = i + 1
                while line[i] != "[":
                    i = i + 1
                i = i + 1
                while line[i] == " ":
                    i = i + 1
                while i < length:
                    if line[i] == ",":
                        cur_list.append(simplifier.create_node(cur))
                        cur = ""
                        i = i + 1
                        continue
                    if line[i] == "]":
                        cur_list.append(simplifier.create_node(cur))
                        cur = ""
                        break
                    if line[i] != " ":
                        cur += line[i]
                    i = i + 1
                simplifier.at_least_helper(cur_list, [], int(count), gate_node, len(cur_list))
        raw.close()

    @staticmethod
    def at_least_helper(neg_list, pos_list, count, gate_node, last_size):  # last_size用于避免得到相同的组合
        if count == 0:
            new_node = simplifier.create_node("al" + str(simplifier.at_least_num))
            simplifier.add_child(gate_node, new_node)
            simplifier.at_least_num += 1
            new_node.gate_type = simplifier.operator_tag["&"]
            for pos in pos_list:
                new_node.children.append(pos)
            for neg in neg_list:
                new_node.children.append(simplifier.create_node("-" + neg.name))
            return
        size = len(neg_list)
        while size > 0:
            size -= 1
            if size >= last_size:
                continue
            new_pos_list = []
            new_neg_list = []
            for i in pos_list:
                new_pos_list.append(i)
            new_pos_list.append(neg_list[size])
            for j in neg_list:
                new_neg_list.append(j)
            new_neg_list.remove(neg_list[size])
            simplifier.at_least_helper(new_neg_list, new_pos_list, count - 1, gate_node, size)

    @staticmethod
    def xor_helper(xor_root, first_node, second_node_list):
        flag = True
        if len(second_node_list) == 1:
            flag = False  # 二元异或
        xor_root.gate_type = simplifier.operator_tag["|"]
        simplifier.add_child(xor_root, simplifier.create_node("xo" + str(simplifier.xor_num)))
        simplifier.xor_num += 1
        simplifier.add_child(xor_root, simplifier.create_node("xo" + str(simplifier.xor_num)))
        simplifier.xor_num += 1
        if flag:
            new_xor_root = simplifier.create_node("xo" + str(simplifier.xor_num))
            simplifier.xor_num += 1
        else:
            new_xor_root = second_node_list[0]
        xor_root.children[0].gate_type = xor_root.children[1].gate_type = simplifier.operator_tag["&"]
        neg_a = simplifier.create_node("-" + first_node.name)
        neg_b = simplifier.create_node("-" + new_xor_root.name)
        simplifier.add_child(xor_root.children[0], neg_a)  # ~A & B
        simplifier.add_child(xor_root.children[0], new_xor_root)
        simplifier.add_child(xor_root.children[1], neg_b)  # ~B & A
        simplifier.add_child(xor_root.children[1], first_node)
        if flag:
            return new_xor_root

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
                i -= 1  # 迭代器失效
            else:
                simplifier.simplify(cur_node.children[i])
            i += 1

    @staticmethod
    def format(cur_node):
        if not cur_node.children:
            return
        line = ""
        line += cur_node.name
        line += " := ("
        operator = simplifier.inv_operator_tag[cur_node.gate_type]
        for i in cur_node.children:
            line += i.name + " " + operator + " "
        line = line[:len(line) - 3] + ");"
        print(line)
        simplifier.result += line + "\n"
        for i in cur_node.children:
            simplifier.format(i)


if __name__ == "__main__":
    simplifier.parser("./test.dag")
    simplifier.simplify(simplifier.root_node)
    simplifier.format(simplifier.root_node)
    sdag = open("test.sdag", "w")
    sdag.write(simplifier.result)

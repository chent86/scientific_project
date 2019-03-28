# 非没有进行判断，将其作为普通字符(由于节点要共享孩子信息，所以非不能存储在节点中，因为有的非，有的不是非)
# 解决方案可能为：将children设计为二元组，第一项代表符号

inv_operator_tag = {"or": "|", "and": "&", "xor": "#", "not": "-"}


class node:  # 节点
    def __init__(self, name, gate_type = "basic"):
        self.name = name
        self.gate_type = gate_type
        self.children = []


class node_helper:  # 树

    operator_tag = {"|": "or", "&": "and", "#": "xor", "-": "not"}

    def __init__(self):
        self.node_list = []
        self.root_node = node("r1")
        self.xor_num = 0  # 为xor新增的门
        self.at_least_num = 0  # 为at_least新增的门

    def create_node(self, name):
        for i in self.node_list:
            if i.name == name:
                return i
        new_node = node(name)
        self.node_list.append(new_node)
        if name == "r1":
            self.root_node = new_node
        return new_node

    def delete_child(self, parent_node, child_node):
        parent_node.children.remove(child_node)  # 删除父指向子的指针

    def add_child(self, parent_node, child_node):
        already = False
        for i in parent_node.children:
            if i.name == child_node.name:
                already = True
                break
        if not already:
            parent_node.children.append(child_node)
            child_node.parent = parent_node

    def parser(self, file_name):
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
            gate_node = self.create_node(root)
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
                        cur_list.append(self.create_node(cur))
                        cur = ""
                        i = i + 1
                        continue
                    if line[i] == ")" or line[i] == ";":
                        cur_list.append(self.create_node(cur))
                        cur = ""
                        break
                    if line[i] != " ":
                        cur += line[i]
                    i = i + 1
                if operator != "#":
                    gate_node.gate_type = self.operator_tag[operator]
                    for i in cur_list:
                        self.add_child(gate_node, i)
                else:  # 处理多元异或
                    gate_node.gate_type = self.operator_tag["|"]
                    xor_root = gate_node
                    while xor_root:
                        first_node = cur_list[0]
                        cur_list = cur_list[1:]
                        xor_root = self.xor_helper(xor_root, first_node, cur_list)
            else:
                count = ""  # atleast中至少几个为真
                gate_node.gate_type = self.operator_tag["|"]
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
                        cur_list.append(self.create_node(cur))
                        cur = ""
                        i = i + 1
                        continue
                    if line[i] == "]":
                        cur_list.append(self.create_node(cur))
                        cur = ""
                        break
                    if line[i] != " ":
                        cur += line[i]
                    i = i + 1
                self.at_least_helper(cur_list, [], int(count), gate_node, len(cur_list))
        raw.close()

    def at_least_helper(self, neg_list, pos_list, count, gate_node, last_size):  # last_size用于避免得到相同的组合
        if count == 0:
            new_node = self.create_node("al" + str(self.at_least_num))
            self.add_child(gate_node, new_node)
            self.at_least_num += 1
            new_node.gate_type = self.operator_tag["&"]
            for pos in pos_list:
                new_node.children.append(pos)
            for neg in neg_list:
                new_node.children.append(self.create_node("-" + neg.name))
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
            self.at_least_helper(new_neg_list, new_pos_list, count - 1, gate_node, size)

    def xor_helper(self, xor_root, first_node, second_node_list):
        flag = True
        if len(second_node_list) == 1:
            flag = False  # 二元异或
        xor_root.gate_type = self.operator_tag["|"]
        self.add_child(xor_root, self.create_node("xo" + str(self.xor_num)))
        self.xor_num += 1
        self.add_child(xor_root, self.create_node("xo" + str(self.xor_num)))
        self.xor_num += 1
        if flag:
            new_xor_root = self.create_node("xo" + str(self.xor_num))
            self.xor_num += 1
        else:
            new_xor_root = second_node_list[0]
        xor_root.children[0].gate_type = xor_root.children[1].gate_type = self.operator_tag["&"]
        neg_a = self.create_node("-" + first_node.name)
        neg_b = self.create_node("-" + new_xor_root.name)
        self.add_child(xor_root.children[0], neg_a)  # ~A & B
        self.add_child(xor_root.children[0], new_xor_root)
        self.add_child(xor_root.children[1], neg_b)  # ~B & A
        self.add_child(xor_root.children[1], first_node)
        if flag:
            return new_xor_root
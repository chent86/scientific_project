

class node:  # 节点
    def __init__(self, name, gate_type = "basic"):
        self.name = name
        self.gate_type = gate_type  # and, or
        self.children = set()
        self.sign = dict()  # name : 0为正, 1为负 用来标记孩子的符号

    def __repr__(self):
        return self.name


class node_helper:  # 树

    operator_tag = {"|": "or", "&": "and", "#": "xor", "-": "not"}
    inv_operator_tag = {"or": "|", "and": "&", "xor": "#", "not": "-"}

    def __init__(self):
        self.node_dict = dict()  # name : node
        self.root_node = node("r1")
        self.xor_num = 1  # 为xor新增的门
        self.at_least_num = 1  # 为at_least新增的门
        self.neg_num = 1  # 为负的gate新增的门
        self.output = ""
        self.printed_node = set()
        self.gate_num = 0
        self.basic_num = 0
        self.conflict_num = 0  # 为 e1 & -e1中的-e1添加的门

    def create_node(self, name):
        if name[0] == '-':  # 非与原始的节点是同一个节点，不重复创建
            name = name[1:]
        if name in self.node_dict:
            return self.node_dict.get(name)
        new_node = node(name)
        self.node_dict[name] = new_node
        if name == "r1":
            self.root_node = new_node
        return new_node

    def delete_child(self, parent_node, child_node):
        parent_node.children.remove(child_node)  # 删除父指向子的指针
        parent_node.sign.pop(child_node.name)  # 删除该孩子的符号

    def add_child(self, parent_node, child_node, sign):
        parent_node.children.add(child_node)
        parent_node.sign[child_node.name] = sign

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
            sign_list = []  # 每个child是否取非
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
                        if cur[0] == '-':
                            sign_list.append(1)
                        else:
                            sign_list.append(0)
                        cur = ""
                        i = i + 1
                        continue
                    if line[i] == ")" or line[i] == ";":
                        cur_list.append(self.create_node(cur))
                        if cur[0] == '-':
                            sign_list.append(1)
                        else:
                            sign_list.append(0)
                        cur = ""
                        break
                    if line[i] != " ":
                        cur += line[i]
                    i = i + 1
                if operator != "#":
                    gate_node.gate_type = self.operator_tag[operator]
                    i = 0
                    while i < len(cur_list):
                        if sign_list[i] == 1:
                            has_pos = False
                            for j in range(0, len(cur_list)):
                                if cur_list[j] == cur_list[i] and sign_list[j] == 0:
                                    has_pos = True
                                    break
                            if has_pos:
                                self.conflict_num += 1
                                conflict_node = self.create_node("con" + str(self.conflict_num))
                                conflict_node.gate_type = "and"
                                self.add_child(conflict_node, cur_list[i], sign_list[i])
                                cur_list.append(conflict_node)
                                sign_list.append(0)
                                j = i
                                n = cur_list[i]
                                while j < len(cur_list):
                                    if cur_list[j] == n and sign_list[j] == 1:
                                        del cur_list[j]
                                        del sign_list[j]
                                    else:
                                        j += 1
                                i -= 1
                        i += 1
                    for i in range(len(cur_list)):
                        self.add_child(gate_node, cur_list[i], sign_list[i])
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
                for pos_num in range(int(count), len(cur_list) + 1):
                    self.at_least_helper(cur_list, [], pos_num, gate_node, len(cur_list))
        raw.close()
        self.get_gate_and_basic_num()

    def at_least_helper(self, neg_list, pos_list, count, gate_node, last_size):  # last_size用于避免得到相同的组合（不同的排列）
        if count == 0:
            new_node = self.create_node("al" + str(self.at_least_num))
            self.add_child(gate_node, new_node, 0)
            self.at_least_num += 1
            new_node.gate_type = self.operator_tag["&"]
            for pos in pos_list:
                self.add_child(new_node, pos, 0)
            for neg in neg_list:
                self.add_child(new_node, neg, 1)
            return
        size = len(neg_list)
        while size > 0:  # 对于长度为n的序列，挑一个有n中可能，每一种都要跑一次递归
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
        xo_first = self.create_node("xo" + str(self.xor_num))
        self.add_child(xor_root, xo_first, 0)
        self.xor_num += 1
        xo_second = self.create_node("xo" + str(self.xor_num))
        self.add_child(xor_root, xo_second, 0)
        self.xor_num += 1
        if flag:
            new_xor_root = self.create_node("xo" + str(self.xor_num))
            self.xor_num += 1
        else:
            new_xor_root = second_node_list[0]
        xo_first.gate_type = xo_second.gate_type = self.operator_tag["&"]
        self.add_child(xo_first, first_node, 1)  # ~A & B
        self.add_child(xo_first, new_xor_root, 0)
        self.add_child(xo_second, new_xor_root, 1)  # ~B & A
        self.add_child(xo_second, first_node, 0)
        if flag:
            return new_xor_root

    def format(self, cur_node: node):
        if not cur_node.children:
            return
        if cur_node.name not in self.printed_node:
            self.printed_node.add(cur_node.name)
            line = ""
            line += cur_node.name
            line += " := ("
            operator = self.inv_operator_tag[cur_node.gate_type]
            for child in cur_node.children:
                name = child.name
                if cur_node.sign[name] == 1:
                    line += "-"
                line += name + " " + operator + " "
            line = line[:len(line) - 3] + ");"
            # print(line)
            self.output += line + "\n"
        for i in cur_node.children:
            self.format(i)

    def get_gate_and_basic_num(self):
        for n in self.node_dict.values():
            if n.children:
                self.gate_num += 1
            else:
                self.basic_num += 1

    def no_neg_gate_process(self):
        self.no_neg_helper(self.root_node)

    def no_neg_helper(self, cur_node: node):
        neg_nodes = set()
        for name, node_sign in cur_node.sign.items():
            if node_sign and self.node_dict[name].children:
                neg_nodes.add(self.node_dict.get(name))
        for n in neg_nodes:
            new_node = self.create_node(f"ng{self.neg_num}")
            self.neg_num += 1
            if n.gate_type == "and":
                new_node.gate_type = "or"
            else:
                new_node.gate_type = "and"
            for name, node_sign in n.sign.items():
                new_node.sign[name] = (node_sign + 1) % 2
            for child in n.children:
                new_node.children.add(child)
            self.add_child(cur_node, new_node, 0)
        for n in neg_nodes:
            self.delete_child(cur_node, n)
        for child in cur_node.children:
            self.no_neg_helper(child)

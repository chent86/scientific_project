# 将非考虑为不同的event
# todo: 支持多元异或，对于n元异或，分为n-1个门
# todo: 支持atleast, 使用递归


class node:
    name = ""
    gate_type = ""
    children = []
    def __init__ (self, name, gate_type = "basic"):
        self.name = name
        self.gate_type = gate_type
        self.children = [] # 不再此self就是静态变量

node_list = []
operator_tag = {"|":"or", "&":"and", "#":"xor", "-":"not"}

def create_node(name):
    created = False
    for i in node_list:
        if i.name == name:
            created = True
            break
    if not created:
        node_list.append(node(name))

def delete_child(name, child_name):
    for i in node_list:
        if i.name == name:
            for j in i.children:
                if j.name == child_name:
                    i.children.remove(j) # 删除父指向子的指针
                    node_list.remove(j)  # 将子从节点集合删除
                    break
            break 

def update_gate(name, gate_type):
    for i in node_list:
        if i.name == name:
            i.gate_type = gate_type
            break

def add_child(name, child_name):
    for i in node_list:
        if i.name == name:
            parent = i
            break
    already = False
    for i in parent.children:
        if i.name == child_name:
            already = True
            break
    if not already:
        for i in node_list:
            if i.name == child_name:
                parent.children.append(i)

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
        create_node(root)
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
                    cur_list.append(cur)
                    cur = ""
                    i = i+1
                    continue
                if line[i] == ")" or line[i] == ";":
                    cur_list.append(cur)
                    cur = ""
                    break
                if line[i] != " ":
                    cur += line[i]
                i = i+1
            update_gate(root, operator_tag[operator])
            for i in cur_list:
                create_node(i)
                add_child(root, i)       
    raw.close()

def dfs(cur_node):
    if len(cur_node.children) == 0:
        return
    if len(cur_node.children) == 1:
        tmp_name = cur_node.children[0].name
        tmp_children = cur_node.children[0].children
        delete_child(cur_node.name, cur_node.children[0].name)
        cur_node.name = tmp_name
        cur_node.children = tmp_children
        return
    i = 0
    while i < len(cur_node.children):
        if cur_node.gate_type == cur_node.children[i].gate_type:
            for j in cur_node.children[i].children:
                cur_node.children.append(j)
            delete_child(cur_node.name, cur_node.children[i].name)
            i -= 1 #迭代器失效
        else:
            dfs(cur_node.children[i])
        i += 1

def simplify():
    root_node = ""
    for i in node_list:
        if i.name == "r1":
            root_node = i
            break
    dfs(root_node)

parser("./motor2.dag")

simplify()
for i in node_list:
    print("@", i.name)
    for j in i.children:
        print("-", j.name)

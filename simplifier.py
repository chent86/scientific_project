from tools import node_helper
import os
import sys


class simplifier:
    def __init__(self, helper: node_helper, r1 = True, r2 = True, r3 = True):
        self.helper = helper
        self.r1 = r1  # 合并相邻相同的门
        self.r2 = r2  # 合并单输入门
        self.r3 = r3  # 合并相同子树

    def simplify(self):
        visited_set = set()
        if self.r1 or self.r2 or self.r3:
            self.simplify_helper(self.helper.root_node, None, visited_set)

    def simplify_helper(self, cur_node, parent_node, visited_set):
        if len(cur_node.children) == 0:
            return
        children_list = [child for child in cur_node.children]  # 避免迭代器失效
        i = 0
        while i < len(children_list):
            child = children_list[i]
            if child not in cur_node.children:
                print(child, "not the child of", cur_node)
                i += 1
                continue
            if len(child.children) == 1 and self.r2:
                for new_child in child.children:
                    break
                sign = child.sign[new_child.name]
                if new_child.name in cur_node.sign and cur_node.sign[new_child.name] != sign:
                    print("error! not and origin in same gate")
                    sys.exit()
                self.helper.add_child(cur_node, new_child, sign)  # 不进行深拷贝，因为这样会导致同名的不同节点，造成同步困难
                self.helper.delete_child(cur_node, child)
                children_list.remove(child)
                children_list.append(new_child)
                continue
            if cur_node.gate_type == child.gate_type and self.r1:
                for j in child.children:
                    cur_sign = child.sign[j.name]
                    self.helper.add_child(cur_node, j, cur_sign)
                    if j not in children_list:
                        children_list.append(j)
                self.helper.delete_child(cur_node, child)
                children_list.remove(child)
                continue
            else:
                self.simplify_helper(child, cur_node, visited_set)
                if self.r3 and child.children:  # 从最倒数第二层子树开始考虑, 自底向上合并等效的节点
                    flag = True
                    for visited_node in visited_set:
                        if visited_node.name == child.name:
                            flag = False
                            break
                        if visited_node.gate_type == child.gate_type:
                            if visited_node.sign == child.sign:
                                sign = cur_node.sign.get(child.name)
                                self.helper.delete_child(cur_node, child)
                                self.helper.add_child(cur_node, visited_node, sign)
                                children_list[i] = visited_node
                                flag = False
                                break
                    if flag:
                        visited_set.add(children_list[i])
            i += 1
        # 合并相同节点后需要再次判断
        if len(cur_node.children) == 1 and self.r2:
            for new_child in cur_node.children:
                break
            sign = cur_node.sign[new_child.name]
            if parent_node and new_child.name in parent_node.sign and parent_node.sign[new_child.name] != sign:
                print("error! not and origin in same gate")
                sys.exit()
            if parent_node:
                self.helper.add_child(parent_node, new_child, sign)  # 不进行深拷贝，因为这样会导致同名的不同节点，造成同步困难
                self.helper.delete_child(parent_node, cur_node)
                cur_node = new_child
            else:  # cur_node为r1
                cur_node.children = new_child.children
                cur_node.sign = new_child.sign
        children_list = [child for child in cur_node.children]
        if self.r1:
            i = 0
            while i < len(children_list):
                child = children_list[i]
                if cur_node.gate_type == child.gate_type:
                    for j in child.children:
                        cur_sign = child.sign[j.name]
                        self.helper.add_child(cur_node, j, cur_sign)
                        children_list.append(j)
                    self.helper.delete_child(cur_node, child)
                    children_list.remove(child)
                    i -= 1
                i += 1


def handler_func(input_file_dir, output_file_dir, file_name, r1 = True, r2 = True, r3 = True):
    h = node_helper()
    h.parser(input_file_dir + file_name + ".dag")
    s = simplifier(h, r1, r2, r3)
    s.simplify()
    h.format(h.root_node)
    os.system("mkdir data/result/" + file_name)
    sdag = open(output_file_dir + "/" + file_name + "/" + file_name + ".sdag", "w")
    sdag.write(h.output)
    return s

from tools import node_helper
import os
import sys


class simplifier:
    def __init__(self, helper: node_helper):
        self.helper = helper

    def simplify(self):
        visited_set = set()
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
            if len(child.children) == 1:  # 孩子数为1，则向上合并。需要注意，更新节点名称是全局的，但是更新sign只是局部的
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
            if cur_node.gate_type == child.gate_type:
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
                if child.children:  # 从最倒数第二层子树开始考虑, 自底向上合并等效的节点
                    flag = True
                    for visited_node in visited_set:
                        if visited_node == child:  # 化简单个孩子时，会产生同名的不同地址的相同节点，这种也要化简
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
        if len(cur_node.children) == 1:
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

    def update_all_sign(self, old_name, new_name):
        for key in self.helper.node_dict:
            cur_node = self.helper.node_dict[key]
            if old_name in cur_node.sign:
                cur_node.sign[new_name] = cur_node.sign[old_name]
                cur_node.sign.pop(old_name)


def handler_func(input_file_dir, output_file_dir, file_name):
    h = node_helper()
    h.parser(input_file_dir + file_name + ".dag")
    s = simplifier(h)
    s.simplify()
    h.format(h.root_node)
    os.system("mkdir data/result/" + file_name)
    sdag = open(output_file_dir + "/" + file_name + "/" + file_name + ".sdag", "w")
    sdag.write(h.output)

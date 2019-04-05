from tools import node_helper
import os


class simplifier:
    def __init__(self, helper: node_helper):
        self.helper = helper

    def simplify(self, cur_node):
        visited_set = set()
        self.simplify_helper(cur_node, visited_set)

    def simplify_helper(self, cur_node, visited_set):
        if len(cur_node.children) == 0:
            return
        children_list = [child for child in cur_node.children]  # 避免迭代器失效
        i = 0
        while i < len(children_list):
            child = children_list[i]
            if len(child.children) == 1:  # 孩子数为1，则向上合并。需要注意，更新节点名称是全局的，但是更新sign只是局部的
                for new_child in child.children:
                    break
                child.gate_type = new_child.gate_type  # 要进行深拷贝
                child.children = new_child.children
                cur_node.sign[new_child.name] = child.sign[new_child.name]
                cur_node.sign.pop(child.name)
                child.sign = new_child.sign
                self.update_all_sign(child.name, new_child.name)  # 将等价性扩展到所有节点的符号dict(sign)
                child.name = new_child.name

            if cur_node.gate_type == child.gate_type:
                for j in child.children:
                    cur_sign = child.sign[j.name]
                    self.helper.add_child(cur_node, j, cur_sign)
                    if j not in children_list:
                        children_list.append(j)
                self.helper.delete_child(cur_node, child)
                children_list.remove(child)
                i -= 1
            else:
                self.simplify_helper(child, visited_set)
                if child.children:  # 从最倒数第二层子树开始考虑, 自底向上合并等效的节点
                    flag = True
                    for visited_node in visited_set:
                        if visited_node.name == child.name:
                            flag = False
                            break
                        if visited_node.gate_type == child.gate_type:
                            if visited_node.sign == child.sign:
                                sign = cur_node.sign.get(child.name)
                                cur_node.sign.pop(child.name)
                                cur_node.sign[visited_node.name] = sign
                                cur_node.children.remove(child)
                                cur_node.children.add(visited_node)
                                flag = False
                                break
                    if flag:
                        visited_set.add(children_list[i])
            i += 1
        # 合并相同节点后需要再次判断
        if len(cur_node.children) == 1:
            for expire_child in cur_node.children:
                break
            cur_node.gate_type = expire_child.gate_type
            cur_node.children = expire_child.children
            cur_node.sign = expire_child.sign
            self.update_all_sign(cur_node.name, expire_child.name)
            cur_node.name = expire_child.name
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
    s.simplify(h.root_node)
    h.format(h.root_node)
    os.system("mkdir data/result/" + file_name)
    sdag = open(output_file_dir + "/" + file_name + "/" + file_name + ".sdag", "w")
    sdag.write(h.output)

import simplifier
import find_modules
import os
import traceback
import time
import pickle
from config import SAME_GATE, ONE_CHILD, SAME_TREE, LCC_PROCESS, SIMPLE_OUTPUT

if __name__ == "__main__":
    input_file_dir = "data/raw/"
    output_file_dir = "data/result/"
    os.system("rm -rf data/result")
    os.system("mkdir data/result")
    for root, dirs, files in os.walk(input_file_dir):
        break
    slow = ["nus9601", "das9701", "elf9601", "edf9206"]
    # slow = []
    # files = ["chinese.dag"]
    for file_name in files:
        begin_time = time.time()
        name = file_name[:len(file_name) - 4]
        print(name, end='\r')
        if name in slow:
            continue
        try:
            s = simplifier.handler_func(input_file_dir, output_file_dir, name, SAME_GATE, ONE_CHILD, SAME_TREE)
            simplify_end_time = time.time()
            print(name, "->", "【simplify time】", simplify_end_time - begin_time, end='\r')
            handler = find_modules.handler(output_file_dir, output_file_dir, name, LCC_PROCESS, SIMPLE_OUTPUT)
            handler.origin_basic_event_num = s.helper.basic_num
            handler.origin_gate_event_num = s.helper.gate_num
            data = handler.data()
            data_file = open(f"{output_file_dir}{name}/pickle_data", "wb")
            pickle.dump(data, data_file, 2)
            # print(data)
            module_end_time = time.time()
            print(name, "->", "【simplify time】", simplify_end_time - begin_time,
                  "【module time】", module_end_time - simplify_end_time, "【module】", data["modules_num"])
        except Exception:
            print(name, "error!!")
            traceback.print_exc()

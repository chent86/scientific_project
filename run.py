import simplifier
import find_modules
import os


if __name__ == "__main__":
    input_file_dir = "data/raw/"
    output_file_dir = "data/result/"
    os.system("rm -rf data/result")
    os.system("mkdir data/result")
    for root, dirs, files in os.walk(input_file_dir):
        break
    slow = ["nus9601", "das9701", "elf9601", "edf9206"]
    err = []
    for file_name in files:
        name = file_name[:len(file_name) - 4]
        print(name)
        if name in slow:
            continue
        simplifier.handler_func(input_file_dir, output_file_dir, name)
        handler = find_modules.handler(output_file_dir, output_file_dir, name)
        data = handler.data()
    print(err)

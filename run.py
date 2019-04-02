import simplifier
import find_modules
import os


if __name__ == "__main__":
    input_file_dir = "data/abc/"
    output_file_dir = "data/result/"
    os.system("rm -rf data/result")
    os.system("mkdir data/result")
    for root, dirs, files in os.walk(input_file_dir):
        break

    for file_name in files:
        name = file_name[:len(file_name) - 4]
        simplifier.handler_func(input_file_dir, output_file_dir, name)
        handler = find_modules.handler(output_file_dir, output_file_dir, name)
        data = handler.data()

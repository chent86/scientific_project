import os
import re
import xlwt
CASE_DIR = "study_cover"
CASE1 = "CoAFTA"
CASE2 = "XFTA"


def get_dict(case):
    result = dict()
    for root, dirs, files in os.walk(f"{CASE_DIR}/{case}"):
        break
    # files = ["gensys-brn11.mcs"]
    for f in files:
        print("prepare set", case, f)
        s = set()
        raw = open(f"{CASE_DIR}/{case}/{f}")
        for line in raw:
            t = re.split(" |\t|\n", line)
            while t[-1] == "":
                del t[-1]
            t.sort(key=lambda x: int(x[1:]))
            s.add(" ".join(t))
            # print(t)
        # return None
        result[f] = s
    return result


def comp(case_a, dict_a, case_b, dict_b):
    detail_dict = dict()
    count_dict = dict()
    for file_name, s in dict_a.items():
        detail_dict[file_name] = dict()
        detail_dict[file_name][f"{case_a}_only"] = dict_a[file_name] - dict_b[file_name]
        detail_dict[file_name][f"{case_b}_only"] = dict_b[file_name] - dict_a[file_name]
        detail_dict[file_name]["common"] = dict_a[file_name] & dict_b[file_name]

        count_dict[file_name] = dict()
        count_dict[file_name][f"{case_a}_only"] = len(detail_dict[file_name][f"{case_a}_only"])
        count_dict[file_name][f"{case_b}_only"] = len(detail_dict[file_name][f"{case_b}_only"])
        count_dict[file_name]["common"] = len(detail_dict[file_name]["common"])
    return detail_dict, count_dict


def output_excel(count_dict):
    wb = xlwt.Workbook(encoding = 'ascii')
    ws = wb.add_sheet('My Worksheet')
    ws.write(0, 1, "CoAFTA_only")
    ws.write(0, 2, "XFTA_only")
    ws.write(0, 3, "common")
    xls_line = 0
    for file_name, d in count_dict.items():
        xls_line += 1
        ws.write(xls_line, 0, file_name[:len(file_name) - 4])
        ws.write(xls_line, 1, d["CoAFTA_only"])
        ws.write(xls_line, 2, d["XFTA_only"])
        ws.write(xls_line, 3, d["common"])
    wb.save("count.xls")


def file_write_set_data(file_name, s):
    file = open(file_name, "w")
    for d in s:
        file.write(d + "\n")
    file.close()


def output_detail(detail_dict):
    os.system("rm -rf detail")
    os.system("mkdir detail")
    for file_name, d in detail_dict.items():
        f = file_name[:len(file_name) - 4]
        os.system(f"mkdir detail/{f}")
        file_write_set_data(f"detail/{f}/CoAFTA_only", d["CoAFTA_only"])
        file_write_set_data(f"detail/{f}/XFTA_only", d["XFTA_only"])
        file_write_set_data(f"detail/{f}/common", d["common"])


if __name__ == "__main__":
    dict_a = get_dict(CASE1)
    dict_b = get_dict(CASE2)
    detail_dict, count_dict = comp(CASE1, dict_a, CASE2, dict_b)
    print(count_dict)
    output_excel(count_dict)
    output_detail(detail_dict)

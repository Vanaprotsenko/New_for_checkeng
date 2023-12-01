import os
import re

from intelhex import IntelHex


def search_id_address(firmware: str) -> int:
    try:
        return int(re.findall(r"0x[\dA-Fa-f]*", firmware)[0], 16)
    except IndexError:
        raise ValueError("no ID address in fw name") from None


def merge_files(file1_boot: str, file2_firm: str) -> str:
    boot = IntelHex()
    firm = IntelHex()
    merge = IntelHex()
    boot.fromfile(file1_boot, format='hex')
    firm.fromfile(file2_firm, format='hex')

    merge.merge(boot, overlap='error')
    merge.merge(firm, overlap='replace')

    #  NAME FINAL FILE
    path = os.path.abspath(os.path.dirname(file1_boot))
    merge_name = os.path.join(path, "MERGED.hex")
    merge.write_hex_file(merge_name)
    return merge_name


def delete_line(file: str, line_num: int) -> str:
    with open(file, "r") as f:
        lines = f.readlines()
    with open(file, "w") as f:
        for i, line in enumerate(lines, start=1):
            i != line_num and f.write(line)
    return file

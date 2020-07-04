import random
import string

from prettytable import PrettyTable


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def print_dir_info(info_list):
    table = PrettyTable()
    table.field_names = ['名称', '类型', '大小']
    for item in info_list:
        if item['isdir'] == 1:
            f_type = '文件夹'
        else:
            f_type = '文件'
        file_size = sizeof_fmt(item['size'])
        table.add_row([item['server_filename'], f_type, file_size])
    print(table)


def random_str(num):
    salt = ''.join(random.sample(string.ascii_letters + string.digits, num))
    return salt

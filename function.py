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


def trans_info_to_path(info: list):
    path_list = []
    for item in info:
        f_path = item['path']
        path_list.append(f_path)
    return path_list


def help_c():
    print(
        '说明："[]"表示非必须 输入help显示本说明\n'
        '可以使用以下命令\n'
        'rm params 删除文件或文件夹(注意：直接删除不会提示！！！) 可用"*"表示删除所有内容\n'
        'rename old_name new_name 重命名文件或文件夹\n'
        'download [params] 下载当前文件夹所有内容或指定内容\n'
        'cd [params] 切换至指定目录，不指定则返回根目录\n'
        'switch 切换至其他已存储账号\n'
        'exit 退出程序\n'
        'logout 删除当前账号信息并返回设置\n'
        'reftk 刷新当前账号access_token'
    )

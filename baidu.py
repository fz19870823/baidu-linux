import configparser
# import re
import sys
import shlex
import webbrowser
# import getopt

import aria2
from account import Account
from function import *

headers = {
    'User-Agent': 'pan.baidu.com'
}
config = configparser.ConfigParser()
config.read('config.ini')
client_id = config['api_config']['client_id']
client_secret = config['api_config']['client_secret']


def login():
    while True:
        name = input('输入账户名称：')
        if name is not 'api_config' and name is not 'aria2':
            break
        print('预置变量名，不可使用，请换用其他名字')
    newaccount = Account(name)
    # 使用code方式获取授权token
    try:
        webbrowser.open('https://openapi.baidu.com/oauth/2.0/authorize?response_type=code&client_id='
                        '%s&redirect_uri=oob&scope=basic,netdisk&display=tv&qrcode=1&'
                        'force_login=1' % client_id)
    except Exception as e:
        print(e)
        print('无法打开浏览器，请手动打开以下网页获取code：\n'
              'https://openapi.baidu.com/oauth/2.0/authorize?response_type=code&client_id='
              '%s&redirect_uri=oob&scope=basic,netdisk&display=tv&qrcode=1&'
              'force_login=1' % client_id
              )
    code = input('输入获取的code：')
    newaccount.get_account_info(code)
    newaccount.save_account_info()
    return newaccount


def load():
    accounts_list = config.sections()
    accounts_list.remove('api_config')
    accounts_list.remove('aria2')
    i = 1
    print('有以下账号，请选择使用的账号：')
    for account_name in accounts_list:
        print('%s. %s' % (i, account_name))
        i += 1
    try:
        account_no = int(input('输入序号：'))
    except Exception as e:
        print(e)
        return
    if account_no <= len(accounts_list):
        account_old = Account(accounts_list[account_no - 1])
    else:
        print('不存在的序号！')
        return
    account_old.read_account_info()
    return account_old


def start():
    command_s = input('输入命令开始\n1. 从配置文件中读取配置\n2. 配置新的账号\n输入序号：')
    if command_s == '2':
        account_s = login()
    elif command_s == '1':
        account_s = load()
    else:
        print('错误的命令')
        account_s = start()
    return account_s


while True:
    account = start()
    while account is not None:
        current_dir = account.current_dir
        commands = input('现在所在目录：%s 命令：' % current_dir)
        argv = shlex.split(commands)
        command = argv[0]
        if command == 'ls':
            try:
                path = argv[1]
                dir_info = account.dir_list_info(path)
            except IndexError:
                dir_info = account.current_dir_list()
            print_dir_info(dir_info)
        elif command == 'cd':
            try:
                des_folder = argv[1]
            except IndexError:
                des_folder = '/'
            if des_folder == '..':
                des_folder = str(account.parent_dir())
                # print(des_folder)
            else:
                pass
            status = account.check_existing(des_folder)
            if status is 'True':
                account.set_current_dir(des_folder)
            else:
                print(status)
                print('出错，重置为根目录！')
                account.current_dir = '/'
        elif command == 'rm':
            try:
                destination = argv[1]
                account.delete_files(destination)
            except IndexError:
                continue
        elif command == 'download':
            account.set_extractor()
            account.set_fsids()
            link_element = account.extractor.get_dlink()
            aria2.Aria2().add_task(link_element, account.current_dir)
        elif command == 'exit':
            sys.exit()
        elif command == 'switch':
            account = None
        else:
            print('错误的命令！')
        pass

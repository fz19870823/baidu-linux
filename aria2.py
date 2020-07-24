import configparser
import requests
from pathlib import PurePosixPath
from function import random_str

config = configparser.ConfigParser()
config.read('config.ini')
schema = config['aria2']['schema']
rpc = config['aria2']['rpc']
port = config['aria2']['port']
secret = config['aria2']['secret']


class Aria2:

    # 定义 aria2 服务器参数
    def __init__(self):
        self.rpc = rpc
        self.port = port
        self.secret = secret
        self.schema = schema

    def add_task(self, link_container, current_dir):
        headers = 'User-Agent: pan.baidu.com'
        final_post_data = []
        for linke in link_container:
            save_dir = str(PurePosixPath(linke[-1]).relative_to(PurePosixPath(current_dir)))
            # print(save_dir)
            # continue
            formdata = {
                'jsonrpc': '2.0',
                'id': random_str(16),
                'method': 'aria2.addUri',
                'params': ['token:%s' % self.secret, [linke[0]], {'header': headers, 'out': save_dir}]
            }
            final_post_data.append(formdata)
        link = '%s://%s:%s/jsonrpc' % (self.schema, self.rpc, self.port)
        requests.post(link, json=final_post_data)
        # break

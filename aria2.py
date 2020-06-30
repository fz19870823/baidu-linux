import configparser
import requests

config = configparser.ConfigParser()
config.read('config.ini')
schema = config['aria2']['schema']
rpc = config['aria2']['rpc']
port = config['aria2']['port']
secret = config['aria2']['secret']


class Aria2:

    def __init__(self):
        self.rpc = rpc
        self.port = port
        self.secret = secret
        self.schema = schema

    def add_task(self, link_container, current_dir):
        headers = 'User-Agent: pan.baidu.com'
        for linke in link_container:
            save_dir = linke[-1].lower().replace(current_dir.lower(), '')[1:]
            print(save_dir)
            continue
            formdata = {
                'jsonrpc': '2.0',
                'id': 'qwer',
                'method': 'aria2.addUri',
                'params': ['token:%s' % self.secret, [linke[0]], {'header': headers, 'out': save_dir}]
            }
            link = '%s://%s:%s/jsonrpc' % (self.schema, self.rpc, self.port)
            requests.post(link, json=formdata)
            # break

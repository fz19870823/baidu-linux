import requests
import configparser
from extractor import Extractor
from pathlib import PurePosixPath

headers = {
    'User-Agent': 'pan.baidu.com'
}
config = configparser.ConfigParser()
config.read('config.ini')
client_id = config['api_config']['client_id']
client_secret = config['api_config']['client_secret']


class Account:

    def __init__(self, name):
        self.name = name
        self.access_token = None
        self.refresh_token = None
        self.scope = None
        self.current_dir = '/'
        self.current_dir_content = []
        self.extractor = None

    def set_extractor(self):
        self.extractor = Extractor(self.access_token)

    def extract_links(self, fsids):
        self.extractor.get_dlink(fsids)

    def set_account_info(self, access_token, refresh_token, scope):
        self.scope = scope
        self.refresh_token = refresh_token
        self.access_token = access_token

    def set_current_dir(self, path: str):
        if path.startswith('/'):
            pass
        else:
            path = str(PurePosixPath(self.current_dir, path))
            # print(path)
        self.current_dir = path

    def get_account_info(self, code):
        info = requests.get('https://openapi.baidu.com/oauth/2.0/token?grant_type=authorization_code&'
                            'code=%s&client_id=%s&client_secret=%s' % (code, client_id, client_secret)).json()
        self.access_token = info['access_token']
        self.refresh_token = info['refresh_token']
        self.scope = info['scope']

    def save_account_info(self):
        config_new = configparser.ConfigParser()
        config_new[self.name] = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'scope': self.scope
        }
        with open('config.ini', 'a+') as configfile:
            config_new.write(configfile)

    def read_account_info(self):
        access_token = config[self.name]['access_token']
        scope = config[self.name]['scope']
        refresh_token = config[self.name]['refresh_token']
        self.set_account_info(access_token, refresh_token, scope)

    def current_dir_list(self):
        api_url = 'https://pan.baidu.com/rest/2.0/xpan/file?method=list'
        params = {
            'dir': self.current_dir,
            'limit': '1000',
            'folder': '0',
            # 'showempty': '1',
            'access_token': self.access_token
        }
        res = requests.get(api_url, params=params, headers=headers).json()
        info_list = res['list']
        return info_list

    def dir_list_info(self, path: str):
        if path.startswith('/'):
            pass
        else:
            path = self.current_dir + '/' + path
        api_url = 'https://pan.baidu.com/rest/2.0/xpan/file?method=list'
        params = {
            'dir': path,
            'limit': '1000',
            'folder': '0',
            # 'showempty': '1',
            'access_token': self.access_token
        }
        res = requests.get(api_url, params=params, headers=headers).json()
        info_list = res['list']
        return info_list

    def check_existing(self, path: str):
        if path.startswith('/'):
            pass
        else:
            path = str(PurePosixPath(self.current_dir).joinpath(path))
        api_url = 'https://pan.baidu.com/rest/2.0/xpan/file?method=list'
        params = {
            'dir': path,
            'limit': '1000',
            'folder': '0',
            # 'showempty': '1',
            'access_token': self.access_token
        }
        res = requests.get(api_url, params=params, headers=headers).json()
        er_code = res['errno']
        if er_code == 0:
            return 'True'
        elif er_code == -7:
            return '文件或目录名错误或无权访问'
        elif er_code == -9:
            return '文件或目录不存在'
        else:
            return '未知错误，错误代码%s!' % er_code

    def recursive_get_fsids(self):
        api_url = 'https://pan.baidu.com/rest/2.0/xpan/multimedia?method=listall'
        params = {
            'path': self.current_dir,
            'recursion': 1,
            'limit': 100,
            'access_token': self.access_token
        }
        res = requests.get(api_url, headers=headers, params=params).json()
        if res['errno'] == 0:
            fsids = []
            for item in res['list']:
                if item['isdir'] == 0:
                    fsid = item['fs_id']
                    fsids.append(fsid)
            return fsids
        else:
            print('错误，代码%s' % res['errno'])
            print(res)
            return

    def set_fsids(self):
        fids = self.recursive_get_fsids()
        self.extractor.set_fsids(fids)

    def delete_files(self, path):
        if path.startswith('/'):
            pass
        else:
            path = str(PurePosixPath(self.current_dir).joinpath(path))
        api_url = 'https://pan.baidu.com/rest/2.0/xpan/file?method=filemanager'
        params = {
            'access_token': self.access_token,
            'opera': 'delete'
        }
        formdata = {
            'filelist': [path],
            'async': 1
        }
        res = requests.post(api_url, params=params, headers=headers, json=formdata).json()
        print(res)

    def parent_dir(self):
        current_dir = PurePosixPath(self.current_dir)
        parent_dir = str(current_dir.parent)
        return parent_dir

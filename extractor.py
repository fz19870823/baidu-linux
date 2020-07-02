import requests

api_url = 'https://pan.baidu.com/rest/2.0/xpan/multimedia?method=filemetas'
headers = {
    'User-Agent': 'pan.baidu.com'
}


class Extractor:

    def __init__(self, access_token):
        self.access_token = access_token
        self.fsids = None

    def set_fsids(self, fsids):
        self.fsids = fsids

    def get_dlink(self):
        link_container = []
        for fsid_list in [self.fsids[i:i+99] for i in range(0, len(self.fsids), 98)]:
            # print(fsid_list)
            # continue
            params = {
                'access_token': self.access_token,
                'fsids': str(fsid_list),
                'dlink': 1
            }
            response = requests.get(api_url, params=params, headers=headers).json()
            if response['errno'] == 0:
                for item in response['list']:
                    dlink = item['dlink']
                    path = item['path']
                    link_container.append((dlink + '&access_token=%s' % self.access_token, path))
            else:
                print('错误！错误代码%s' % response['errno'])
                print(response)
                return
        return link_container

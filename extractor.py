import requests

api_url = 'https://pan.baidu.com/rest/2.0/xpan/multimedia?method=filemetas'
headers = {
    'User-Agent': 'pan.baidu.com'
}


class Extractor:

    def __init__(self, access_token):
        """
        init Extractor
        param: access_token
        """
        self.access_token = access_token
        self.fsids = None

    def set_fsids(self, fsids):
        print(f'[extractor] set_fsids: {len(fsids) if fsids else 0} 个 fsid')
        self.fsids = fsids

    def get_dlink(self):
        if not self.fsids:
            print('[extractor] fsids 为空, 返回空链接')
            return []
        link_container = []
        batches = [self.fsids[i:i+99] for i in range(0, len(self.fsids), 98)]
        print(f'[extractor] 分 {len(batches)} 批次获取 dlink')
        for fsid_list in batches:
            params = {
                'access_token': self.access_token,
                'fsids': str(fsid_list),
                'dlink': 1
            }
            response = requests.get(api_url, params=params, headers=headers, timeout=15).json()
            if response['errno'] == 0:
                for item in response['list']:
                    dlink = item['dlink']
                    path = item['path']
                    link_container.append((dlink + '&access_token=%s' % self.access_token, path))
                print(f'[extractor] 获取 {len(response["list"])} 个 dlink')
            else:
                print(f'[extractor] 错误! errno={response["errno"]}')
                print(f'[extractor] {response}')
                return
        print(f'[extractor] 共获取 {len(link_container)} 个下载链接')
        return link_container

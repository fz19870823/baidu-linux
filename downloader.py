from requests import Session
# import threading


# not finished
basic_headers = {
    'User-Agent': 'pan.baidu.com'
}


class Downloader:

    def __init__(self, url, file_name, path):
        """
        init downloader
        param: file_name, Path
        """
        self.url = url
        self.threads = 20
        self.path = path
        self.file_name = file_name
        self.headers = []
        self.chunk_size = 5 * 1024 * 1024
        self.size = None
        self.session = Session()

    def download_split(self):
        block_size = int(self.size / self.threads)
        range_list = []
        for threads_number in range(0, self.threads):
            ranges = (threads_number * block_size, (1 + threads_number) * block_size)
            range_list.append(ranges)
        print(range_list)

    def download_prepare(self):
        r = self.session.get(self.url, headers=self.headers, stream=True)
        size = r.headers['Content-Length']
        self.size = size

    # def download_start(self):
    #     res = self.session.get(self.url, headers=self.headers, stream=True)

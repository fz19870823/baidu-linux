import configparser
import requests
from pathlib import PurePosixPath
from function import random_str


class Aria2:
    """aria2 JSON-RPC 客户端 — 每次初始化时重新读取配置"""

    def __init__(self, rpc=None, port=None, secret=None, schema=None, threads=None):
        """
        参数可选：不传则从 config.ini 读取
        """
        cfg = configparser.ConfigParser()
        cfg.read('config.ini', encoding='utf-8')

        if cfg.has_section('aria2'):
            self.rpc = rpc or cfg['aria2'].get('rpc', 'localhost')
            self.port = port or cfg['aria2'].get('port', '6800')
            self.secret = secret or cfg['aria2'].get('secret', '')
            self.schema = schema or cfg['aria2'].get('schema', 'http')
        else:
            self.rpc = rpc or 'localhost'
            self.port = port or '6800'
            self.secret = secret or ''
            self.schema = schema or 'http'

        # 下载线程数：从 download section 优先取，否则默认5
        if threads is None:
            if cfg.has_section('download'):
                threads = int(cfg['download'].get('threads', '5'))
            else:
                threads = 5
        self.threads = threads

    def add_task(self, link_container, current_dir):
        """
        向 aria2 添加下载任务
        :param link_container: [(dlink_url, file_path), ...]
        :param current_dir: 百度网盘当前目录（用于计算相对保存路径）
        """
        # Header 必须是字符串数组格式
        headers = ['User-Agent: pan.baidu.com']

        final_post_data = []
        for dlink_url, file_path in link_container:
            # 计算相对保存路径
            save_rel = str(PurePosixPath(file_path).relative_to(
                PurePosixPath(current_dir)))

            # aria2 参数：
            #   header  — 字符串数组，每个元素为 "Key: Value"
            #   out     — 文件名（含相对路径）
            #   split   — 分片数（多连接加速下载）
            #   max-connection-per-server — 单服务器最大连接数
            options = {
                'header': headers,
                'out': save_rel,
                'split': str(self.threads),
                'max-connection-per-server': str(self.threads),
                'allow-overwrite': 'true',
                'auto-file-renaming': 'false',
            }

            formdata = {
                'jsonrpc': '2.0',
                'id': random_str(16),
                'method': 'aria2.addUri',
                'params': ['token:%s' % self.secret, [dlink_url], options]
            }
            final_post_data.append(formdata)

        endpoint = '%s://%s:%s/jsonrpc' % (self.schema, self.rpc, self.port)
        resp = requests.post(endpoint, json=final_post_data, timeout=10)
        return resp.status_code == 200

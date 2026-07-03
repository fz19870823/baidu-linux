#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Qt 信号链路测试: 使用 UpdatedDownloadWorker 下载 /封过流汗/S01E01.mp4"""

import sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 强制无缓冲输出
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
import configparser
import account as acct

TARGET_PATH = '/封过流汗/S01E01.mp4'
ACCOUNT_NAME = 'fz19870823'

print('=== Qt 信号链路测试 (line-buffered) ===')
print(f'目标: {TARGET_PATH}')

# 导入 GUI 模块
from gui import UpdatedDownloadWorker

app = QApplication(sys.argv)
print('QApplication 创建完毕')

# 加载账户
cfg = configparser.ConfigParser()
cfg.read('config.ini')
print(f'账户: {ACCOUNT_NAME}')
acc = acct.Account(ACCOUNT_NAME)
acc.read_account_info()
print('账户信息读取完毕, 验证 token...')
acc.check_access_token(0)
print('Token 验证通过')

# 获取 fs_id
acc.set_extractor()
acc.current_dir = '/封过流汗'
results = acc.search_files(TARGET_PATH)
fs_id = None
if results:
    for item in results:
        if item['isdir'] == 0 and item['path'] == TARGET_PATH:
            fs_id = item['fs_id']
            break

print(f'fs_id: {fs_id}')

# 创建 worker
worker = UpdatedDownloadWorker(acc, TARGET_PATH, is_dir=False, fs_id=fs_id)

progress_count = [0]
file_done_count = [0]
download_finished_called = [False]

def on_progress(path, done, total):
    progress_count[0] += 1
    if progress_count[0] <= 3 or progress_count[0] % 10 == 0:
        from function import sizeof_fmt
        pct = done * 100 / total if total > 0 else 0
        print(f'  [信号] dl_progress #{progress_count[0]}: '
              f'{sizeof_fmt(done)}/{sizeof_fmt(total)} ({pct:.0f}%)')

def on_file_done(path):
    file_done_count[0] += 1
    print(f'  [信号] dl_file_done: {path}')

def on_finished(success, msg, count):
    download_finished_called[0] = True
    print(f'\n  [信号] download_finished: success={success}, msg={msg}, count={count}')
    # 退出事件循环
    QTimer.singleShot(100, app.quit)

worker.dl_progress.connect(on_progress)
worker.dl_file_done.connect(on_file_done)
worker.download_finished.connect(on_finished)

# 启动 worker
print('启动 Worker...')
worker.start()
print('Worker 已启动')

# 30 分钟超时
QTimer.singleShot(30 * 60 * 1000, lambda: (
    print('\n⏰ 超时!'), app.quit()
))

app.exec()

print(f'\n--- 结果 ---')
print(f'  dl_progress 信号次数: {progress_count[0]}')
print(f'  dl_file_done 信号次数: {file_done_count[0]}')
print(f'  download_finished 已调用: {download_finished_called[0]}')

if progress_count[0] > 0 and download_finished_called[0]:
    print('✅ Qt 信号链路测试通过!')
elif file_done_count[0] > 0 and download_finished_called[0]:
    print('✅ Qt 信号链路测试通过! (文件已存在, 直接跳过)')
else:
    print('❌ 信号链路有问题!')
    if progress_count[0] == 0:
        print('   → dl_progress 从未触发')
    if not download_finished_called[0]:
        print('   → download_finished 从未触发')

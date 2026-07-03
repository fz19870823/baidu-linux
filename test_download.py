#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动化测试: 下载 /封过流汗/S01E01.mp4
绕过 Qt GUI，直接测试下载管线：Token → fsid → dlink → 分块下载 → 验证
"""

import sys, os, time, threading, traceback
from pathlib import PurePosixPath
from queue import Queue, Empty

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import configparser
import requests
import account as acct
from extractor import Extractor
from function import sizeof_fmt

# ═══════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════
TARGET_PATH = '/封过流汗/S01E01.mp4'
ACCOUNT_NAME = 'fz19870823'
THREADS = 4                # 下载线程数
REPORT_INTERVAL = 2 * 1024 * 1024  # 每 2MB 汇报进度
HEADERS = {'User-Agent': 'pan.baidu.com'}


def load_account(name):
    """加载账户，检查 token"""
    cfg = configparser.ConfigParser()
    cfg.read('config.ini')

    if name not in cfg:
        print(f'❌ 未找到账户 [{name}]')
        return None

    acc = acct.Account(name)
    acc.read_account_info()

    # 验证 token
    print(f'  账户: {name}')
    valid = acc.check_access_token(0)
    if not valid:
        print('❌ Token 刷新失败')
        return None

    # 读下载配置
    if cfg.has_section('download'):
        acc.cfg_download = cfg['download']
    else:
        acc.cfg_download = {'save_path': './downloads', 'threads': '5'}
    return acc


def get_dlink_for_file(acc, target_path):
    """获取单文件的下载链接"""
    print(f'\n--- 获取 fsid: {target_path} ---')

    acc.set_extractor()

    # 对文件使用 search_files（比 listall 更直接）
    parent = str(PurePosixPath(target_path).parent)
    acc.current_dir = parent

    results = acc.search_files(target_path)
    fsids = []
    if results:
        for item in results:
            if item['isdir'] == 0 and item['path'] == target_path:
                fsids.append(item['fs_id'])
    print(f'  search_files: {len(fsids)} 个匹配')

    if not fsids:
        # 回退：尝试父目录 listall
        print('  尝试 listall...')
        acc.download_dir = target_path
        fsids = acc.recursive_get_fsids()

    if not fsids:
        print('❌ 未找到目标文件!')
        return None, None

    fs_id = fsids[0]
    print(f'  fs_id: {fs_id}')

    # 获取 dlink
    print('--- 获取 dlink ---')
    acc.extractor.set_fsids([fs_id])
    links = acc.extractor.get_dlink()

    if not links:
        print('❌ 未获取到下载链接!')
        return None, None

    url, rel_path = links[0]
    print(f'  dlink 获取成功')
    print(f'  路径: {rel_path}')
    return url, rel_path


def download_single(url, local, total_size=0):
    """单线程流式下载（QThread 安全，可用作回退）"""
    print(f'\n  [单线程] 开始下载 → {PurePosixPath(local).name}')
    downloaded = 0
    last_report = 0
    t_start = time.time()

    try:
        resp = requests.get(url, headers=HEADERS, stream=True, timeout=60, allow_redirects=True)
        resp.raise_for_status()
        with open(local, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=128 * 1024):
                f.write(chunk)
                downloaded += len(chunk)
                if downloaded - last_report >= REPORT_INTERVAL:
                    last_report = downloaded
                    elapsed = time.time() - t_start
                    speed = downloaded / elapsed if elapsed > 0 else 0
                    if total_size > 0:
                        pct = downloaded * 100 / total_size
                        eta = (total_size - downloaded) / speed if speed > 0 else 0
                        print(f'  [{sizeof_fmt(downloaded)}/{sizeof_fmt(total_size)} {pct:.0f}% '
                              f'{sizeof_fmt(speed)}/s ETA {eta:.0f}s]')
                    else:
                        print(f'  [{sizeof_fmt(downloaded)} {sizeof_fmt(speed)}/s]')
        return downloaded
    except Exception as e:
        print(f'  ❌ 单线程下载失败: {e}')
        traceback.print_exc()
        return 0


def download_chunked(url, local, total_size):
    """多线程分块下载 —— 纯 Python 实现，无 Qt 依赖，含详细调试"""
    threads_count = THREADS
    chunk_size = max(1024 * 1024, total_size // threads_count)
    chunks = []
    for i in range(threads_count):
        start = i * chunk_size
        if i < threads_count - 1:
            end = min(start + chunk_size - 1, total_size - 1)
        else:
            end = total_size - 1
        if start > end:
            continue
        chunks.append((start, end))

    actual_threads = len(chunks)
    print(f'\n  [分块下载] {actual_threads} 线程, 每块 '
          f'~{chunk_size / 1024 / 1024:.0f} MB')

    # 先验证是否支持 Range
    print(f'  验证 Range 支持...')
    test_range_h = {**HEADERS, 'Range': 'bytes=0-0'}
    try:
        r_test = requests.get(url, headers=test_range_h, timeout=15, allow_redirects=False)
        # 跟踪重定向
        redirect_count = 0
        while r_test.status_code in (301, 302, 303, 307, 308) and redirect_count < 5:
            redirect_url = r_test.headers.get('Location', '')
            if not redirect_url:
                break
            r_test = requests.get(redirect_url, headers=test_range_h, timeout=15, allow_redirects=False)
            redirect_count += 1
        range_supported = (r_test.status_code == 206)
        content_range = r_test.headers.get('Content-Range', '')
        print(f'  Range 测试: status={r_test.status_code}, Content-Range={content_range}')
    except Exception as e:
        print(f'  Range 测试异常: {e}, 假设不支持')
        range_supported = False

    if not range_supported:
        print('  ⚠️ 服务器不支持 Range，降级为单线程下载')
        return download_single(url, local, total_size)

    progress_per_chunk = [0] * actual_threads
    lock = threading.Lock()
    tmp_files = [f'{local}.part{i}' for i in range(actual_threads)]
    errors = []
    range_status_codes = {}  # 记录每个块的响应码

    def fetch_chunk(idx, start, end):
        try:
            range_header = f'bytes={start}-{end}'
            h = {**HEADERS, 'Range': range_header}
            r = requests.get(url, headers=h, stream=True, timeout=120, allow_redirects=True)
            range_status_codes[idx] = r.status_code

            if r.status_code == 200:
                # 服务器忽略了 Range，返回了完整文件!
                errors.append(f'块{idx}: 服务器返回200(忽略Range), 下载整个文件')
                # 仍然下载（浪费带宽但能工作）
                with open(tmp_files[idx], 'wb') as f:
                    for data in r.iter_content(chunk_size=64 * 1024):
                        f.write(data)
                        with lock:
                            progress_per_chunk[idx] += len(data)
            elif r.status_code == 206:
                with open(tmp_files[idx], 'wb') as f:
                    for data in r.iter_content(chunk_size=64 * 1024):
                        f.write(data)
                        with lock:
                            progress_per_chunk[idx] += len(data)
            else:
                errors.append(f'块{idx}: HTTP {r.status_code}')
        except Exception as e:
            errors.append(f'块{idx}: {e}')

    # 启动线程
    threads_list = []
    for idx, (start, end) in enumerate(chunks):
        t = threading.Thread(target=fetch_chunk, args=(idx, start, end))
        t.daemon = True
        t.start()
        threads_list.append(t)

    t_start = time.time()
    last_log_time = time.time()

    # 轮询进度
    while any(t.is_alive() for t in threads_list):
        with lock:
            total_downloaded = sum(progress_per_chunk)

        now = time.time()
        if now - last_log_time >= 1.0:  # 每秒打印一次
            elapsed = now - t_start
            speed = total_downloaded / elapsed if elapsed > 0 else 0
            pct = total_downloaded * 100 / total_size
            eta = (total_size - total_downloaded) / speed if speed > 0 else 0
            per_chunk = [sizeof_fmt(p) for p in progress_per_chunk]
            print(f'  [{sizeof_fmt(total_downloaded)}/{sizeof_fmt(total_size)} {pct:.0f}% '
                  f'{sizeof_fmt(speed)}/s ETA {eta:.0f}s] 各块: {per_chunk}')
            last_log_time = now

        time.sleep(0.3)

    # 最终状态
    with lock:
        total_downloaded = sum(progress_per_chunk)
    elapsed = time.time() - t_start
    speed = total_downloaded / elapsed if elapsed > 0 else 0
    print(f'  下载线程全部完成: {sizeof_fmt(total_downloaded)} / {sizeof_fmt(total_size)} '
          f'({sizeof_fmt(speed)}/s)')

    # 报告状态码
    if range_status_codes:
        print(f'  Range 响应码: {range_status_codes}')

    for t in threads_list:
        t.join()

    if errors:
        print(f'  ⚠️ 下载错误:')
        for e in errors:
            print(f'    - {e}')
        # 如果有范围忽略错误，用合并来修复
        if any('200' in str(e) for e in errors):
            print('  检测到 Range 被忽略，改用单线程下载...')
            for fname in tmp_files:
                try:
                    os.remove(fname)
                except OSError:
                    pass
            return download_single(url, local, total_size)

    # 合并分块
    print('  合并分块...')
    buf_size = 4 * 1024 * 1024
    merge_start = time.time()
    with open(local, 'wb') as out:
        for fname in tmp_files:
            try:
                with open(fname, 'rb') as src:
                    while True:
                        chunk = src.read(buf_size)
                        if not chunk:
                            break
                        out.write(chunk)
            except FileNotFoundError:
                print(f'    ⚠️ 缺少分块: {fname}')

    print(f'  合并完成 (耗时 {time.time() - merge_start:.1f}s)')

    # 清理
    for fname in tmp_files:
        try:
            os.remove(fname)
        except OSError:
            pass

    return total_downloaded


def verify_file(local, expected_size):
    """验证下载完整性"""
    if not os.path.exists(local):
        print(f'❌ 文件不存在: {local}')
        return False

    actual_size = os.path.getsize(local)
    print(f'\n--- 验证 ---')
    print(f'  文件: {PurePosixPath(local).name}')
    print(f'  大小: {sizeof_fmt(actual_size)}')

    if expected_size > 0:
        if actual_size == expected_size:
            print(f'  ✅ 大小匹配!')
            return True
        else:
            diff = actual_size - expected_size
            print(f'  ⚠️ 大小不匹配! 差异: {sizeof_fmt(abs(diff))}')
            return False
    else:
        print(f'  ✅ 下载完成 (无预期大小)')
        return actual_size > 0


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════

def main():
    print('=' * 60)
    print('  baidu-linux 下载自动化测试')
    print(f'  目标: {TARGET_PATH}')
    print('=' * 60)

    # 1. 加载账户
    print('\n[1/4] 加载账户')
    acc = load_account(ACCOUNT_NAME)
    if not acc:
        return 1

    # 2. 获取下载链接
    print('\n[2/4] 获取下载链接')
    url, rel_path = get_dlink_for_file(acc, TARGET_PATH)
    if not url:
        return 1

    # 3. 获取文件大小
    print('\n[3/4] 检查文件信息')
    try:
        head = requests.head(url, headers=HEADERS, timeout=15, allow_redirects=True)
        total_size = int(head.headers.get('Content-Length', 0))
        print(f'  Content-Length: {sizeof_fmt(total_size)} ({total_size} bytes)')
        print(f'  Content-Type: {head.headers.get("Content-Type", "unknown")}')
    except Exception as e:
        print(f'  ⚠️ HEAD 请求失败: {e}')
        total_size = 0

    # 准备保存路径
    save_path = acc.cfg_download.get('save_path', './downloads')
    local = os.path.join(save_path, rel_path.lstrip('/'))
    os.makedirs(os.path.dirname(local) if os.path.dirname(local) else save_path, exist_ok=True)
    print(f'  保存到: {local}')

    # 断点续传检查
    if os.path.exists(local):
        existing = os.path.getsize(local)
        if total_size > 0 and existing == total_size:
            print(f'  ✅ 文件已存在且完整, 跳过下载')
            return 0
        else:
            print(f'  已有不完整文件 ({sizeof_fmt(existing)}), 重新下载')
            os.remove(local)

    # 4. 下载
    print('\n[4/4] 开始下载')
    t0 = time.time()

    if total_size == 0:
        downloaded = download_single(url, local, total_size)
    else:
        downloaded = download_chunked(url, local, total_size)

    elapsed = time.time() - t0
    print(f'\n  总耗时: {elapsed:.1f}s')

    # 验证
    success = verify_file(local, total_size)
    if success:
        print(f'\n🎉 测试通过!')
        return 0
    else:
        print(f'\n💥 测试失败!')
        return 1


if __name__ == '__main__':
    sys.exit(main())

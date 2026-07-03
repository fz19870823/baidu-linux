#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
baidu-linux GUI — 百度网盘 PySide6 客户端
设计系统：Slate 中性色 + Emerald 强调色，深灰文字，干净表面
"""

import configparser
import sys
from datetime import datetime
from pathlib import PurePosixPath

from PySide6.QtCore import Qt, QThread, Signal, QSize, QTimer, QRect, QObject
from PySide6.QtGui import (
    QAction, QFont, QPainter, QColor, QPen, QBrush, QLinearGradient,
    QCursor, QPalette, QPixmap
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QStatusBar, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QComboBox, QMessageBox,
    QInputDialog, QMenu, QAbstractItemView, QSplitter,
    QFrame, QGroupBox, QSizePolicy, QStyle, QStyleOption,
    QProgressBar, QFileDialog, QScrollArea
)

import account as acct
import aria2
from extractor import Extractor
from function import sizeof_fmt

# ═══════════════════════════════════════════════════════════════════════════
# 设计令牌 (Design Tokens)
# ═══════════════════════════════════════════════════════════════════════════

class Colors:
    """Slate + Emerald 色彩系统 — 无纯黑，饱和度 < 80%"""
    BG          = "#f8fafc"  # slate-50
    BG_CARD     = "#ffffff"  # white card surface
    BG_HEADER   = "#ffffff"
    BORDER      = "#e2e8f0"  # slate-200
    BORDER_HOVER = "#cbd5e1" # slate-300

    ACCENT      = "#059669"  # emerald-600
    ACCENT_HOVER = "#047857" # emerald-700
    ACCENT_BG    = "#ecfdf5" # emerald-50
    ACCENT_BORDER = "#a7f3d0"

    TEXT        = "#1e293b"  # slate-800
    TEXT_SEC    = "#64748b"  # slate-500
    TEXT_DIM    = "#94a3b8"  # slate-400
    WHITE       = "#f8fafc"

    DANGER      = "#dc2626"  # red-600
    DANGER_HOVER = "#b91c1c"
    DANGER_BG    = "#fef2f2"
    DANGER_BORDER = "#fecaca"

    FOLDER      = "#2563eb"  # blue-600
    FOLDER_BG   = "#eff6ff"  # blue-50
    FILE_TEXT    = "#475569" # slate-600

    GREEN_BG    = "#f0fdf4"  # green-50
    GREEN_TEXT  = "#16a34a"  # green-600

    ROW_HOVER   = "#f1f5f9"  # slate-100
    ROW_SELECT  = "#ecfdf5"  # emerald-50

    SHADOW      = "rgba(15, 23, 42, 0.06)"

CONFIG_PATH = 'config.ini'


def reload_config():
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_PATH, encoding='utf-8')
    return cfg


def get_account_names():
    cfg = reload_config()
    return [s for s in cfg.sections() if s not in ('api_config', 'aria2')]


# ═══════════════════════════════════════════════════════════════════════════
# 样式表
# ═══════════════════════════════════════════════════════════════════════════

GLOBAL_STYLE = f"""
QMainWindow {{
    background-color: {Colors.BG};
}}
QMenuBar {{
    background: {Colors.BG_HEADER};
    border-bottom: 1px solid {Colors.BORDER};
    padding: 2px 8px;
    font-size: 13px;
    color: {Colors.TEXT_SEC};
}}
QMenuBar::item {{
    padding: 4px 10px;
    border-radius: 4px;
    margin: 2px 2px;
}}
QMenuBar::item:selected {{
    background: {Colors.BG};
    color: {Colors.TEXT};
}}
QMenu {{
    background: {Colors.BG_CARD};
    border: 1px solid {Colors.BORDER};
    border-radius: 8px;
    padding: 6px;
    margin: 4px 0;
}}
QMenu::item {{
    padding: 6px 32px 6px 14px;
    border-radius: 4px;
    font-size: 13px;
    color: {Colors.TEXT};
}}
QMenu::item:selected {{
    background: {Colors.ACCENT_BG};
    color: {Colors.TEXT};
}}
QMenu::separator {{
    height: 1px;
    background: {Colors.BORDER};
    margin: 4px 8px;
}}
QStatusBar {{
    background: {Colors.BG_HEADER};
    border-top: 1px solid {Colors.BORDER};
    font-size: 12px;
    color: {Colors.TEXT_SEC};
    padding: 2px 12px;
}}
QToolBar {{
    background: {Colors.BG_HEADER};
    border: none;
    border-bottom: 1px solid {Colors.BORDER};
    padding: 6px 8px;
    spacing: 4px;
}}
QToolBar::separator {{
    width: 1px;
    background: {Colors.BORDER};
    margin: 4px 6px;
}}
QTableWidget {{
    background: {Colors.BG_CARD};
    border: 1px solid {Colors.BORDER};
    border-radius: 10px;
    font-size: 13px;
    color: {Colors.TEXT};
    selection-background-color: {Colors.ROW_SELECT};
    selection-color: {Colors.TEXT};
    gridline-color: transparent;
    outline: none;
}}
QTableWidget::item {{
    padding: 8px 14px;
    border-bottom: 1px solid {Colors.BORDER};
}}
QTableWidget::item:hover {{
    background: {Colors.ROW_HOVER};
}}
QTableWidget::item:selected {{
    background: {Colors.ROW_SELECT};
    color: {Colors.TEXT};
}}
QHeaderView::section {{
    background: {Colors.BG_CARD};
    border: none;
    border-bottom: 2px solid {Colors.BORDER};
    padding: 10px 14px;
    font-weight: 600;
    font-size: 12px;
    color: {Colors.TEXT_SEC};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QHeaderView::section:hover {{
    color: {Colors.ACCENT};
}}
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: {Colors.BORDER_HOVER};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {Colors.TEXT_DIM};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {Colors.BORDER_HOVER};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
QProgressBar {{
    border: none;
    background: {Colors.BORDER};
    border-radius: 3px;
    height: 4px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {Colors.ACCENT};
    border-radius: 3px;
}}
"""

TOOLBAR_BTN_STYLE = f"""
QPushButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 13px;
    color: {Colors.TEXT_SEC};
    min-height: 28px;
}}
QPushButton:hover {{
    background: {Colors.BG};
    border-color: {Colors.BORDER};
    color: {Colors.TEXT};
}}
QPushButton:pressed {{
    background: {Colors.BORDER};
    border-color: {Colors.BORDER_HOVER};
}}
"""

TOOLBAR_BTN_PRIMARY_STYLE = f"""
QPushButton {{
    background: {Colors.ACCENT};
    border: none;
    border-radius: 6px;
    padding: 5px 14px;
    font-size: 13px;
    font-weight: 500;
    color: {Colors.WHITE};
    min-height: 28px;
}}
QPushButton:hover {{
    background: {Colors.ACCENT_HOVER};
}}
QPushButton:pressed {{
    background: #046c4e;
}}
"""

TOOLBAR_BTN_DANGER_STYLE = f"""
QPushButton {{
    background: transparent;
    border: 1px solid {Colors.BORDER};
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 13px;
    color: {Colors.DANGER};
    min-height: 28px;
}}
QPushButton:hover {{
    background: {Colors.DANGER_BG};
    border-color: {Colors.DANGER_BORDER};
}}
QPushButton:pressed {{
    background: #fee2e2;
}}
"""

DIALOG_STYLE = f"""
QDialog {{
    background: {Colors.BG_CARD};
}}
QLabel {{
    font-size: 13px;
    color: {Colors.TEXT};
}}
QGroupBox {{
    border: 1px solid {Colors.BORDER};
    border-radius: 10px;
    margin-top: 10px;
    padding-top: 26px;
    padding-bottom: 20px;
    padding-left: 18px;
    padding-right: 18px;
    font-size: 13px;
    font-weight: 600;
    color: {Colors.TEXT_SEC};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    top: -2px;
    padding: 0 6px;
    color: {Colors.TEXT_SEC};
}}
QLineEdit {{
    border: 1px solid {Colors.BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    color: {Colors.TEXT};
    background: {Colors.BG};
    min-height: 18px;
}}
QLineEdit:focus {{
    border-color: {Colors.ACCENT};
    background: {Colors.BG_CARD};
}}
QLineEdit::placeholder {{
    color: {Colors.TEXT_DIM};
}}
QComboBox {{
    border: 1px solid {Colors.BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    color: {Colors.TEXT};
    background: {Colors.BG};
    min-height: 18px;
}}
QComboBox:hover {{
    border-color: {Colors.BORDER_HOVER};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox:disabled {{
    background: {Colors.BG};
    color: {Colors.TEXT_DIM};
}}
"""

REGULAR_BTN_STYLE = f"""
QPushButton {{
    background: {Colors.ACCENT};
    border: none;
    border-radius: 6px;
    padding: 9px 20px;
    font-size: 13px;
    font-weight: 600;
    color: {Colors.WHITE};
    min-height: 22px;
}}
QPushButton:hover {{
    background: {Colors.ACCENT_HOVER};
}}
QPushButton:pressed {{
    background: #046c4e;
}}
QPushButton:disabled {{
    background: #f1f5f9;
    color: #64748b;
    border: 1px solid {Colors.BORDER};
}}
"""

SECONDARY_BTN_STYLE = f"""
QPushButton {{
    background: {Colors.BG_CARD};
    border: 1px solid {Colors.BORDER};
    border-radius: 6px;
    padding: 9px 20px;
    font-size: 13px;
    font-weight: 500;
    color: {Colors.TEXT};
    min-height: 22px;
}}
QPushButton:hover {{
    background: {Colors.BG};
    border-color: {Colors.BORDER_HOVER};
}}
QPushButton:pressed {{
    background: {Colors.BORDER};
}}
QPushButton:disabled {{
    background: #f1f5f9;
    color: #94a3b8;
    border-color: {Colors.BORDER};
}}
"""


# ═══════════════════════════════════════════════════════════════════════════
# 后台工作线程
# ═══════════════════════════════════════════════════════════════════════════

class ListFilesWorker(QThread):
    finished = Signal(list, str)

    def __init__(self, account_obj, path, parent=None):
        super().__init__(parent)
        self.account = account_obj
        self.path = path

    def run(self):
        try:
            result = self.account.current_dir_list() if self.path == '/' else self.account.dir_list_info(self.path)
            self.finished.emit(result, '')
        except Exception as e:
            self.finished.emit([], str(e))


class DeleteWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, account_obj, paths, parent=None):
        super().__init__(parent)
        self.account = account_obj
        self.paths = paths

    def run(self):
        try:
            self.account.delete_files(self.paths)
            self.finished.emit(True, '删除成功')
        except Exception as e:
            self.finished.emit(False, str(e))


class RefreshTokenWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, account_obj, parent=None):
        super().__init__(parent)
        self.account = account_obj

    def run(self):
        try:
            self.account.refresh_ac_token()
            self.finished.emit(True, 'Token 刷新成功')
        except Exception as e:
            self.finished.emit(False, str(e))


class VerifyAccountWorker(QThread):
    """后台验证账户 token 有效性，无效时自动刷新"""
    finished = Signal(object, str)  # (account_obj or None, error_message)

    def __init__(self, account_name, parent=None):
        super().__init__(parent)
        self.account_name = account_name

    def run(self):
        try:
            import account as acct
            acc = acct.Account(self.account_name)
            acc.read_account_info()
            if not acc.check_access_token(0):
                acc.refresh_ac_token()
                if not acc.check_access_token(0):
                    self.finished.emit(None, '账户信息无效，请删除后重新添加')
                    return
            self.finished.emit(acc, '')
        except Exception as e:
            self.finished.emit(None, str(e))


class RenameWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, account_obj, old_name, new_name, parent=None):
        super().__init__(parent)
        self.account = account_obj
        self.old_name = old_name
        self.new_name = new_name

    def run(self):
        try:
            self.account.rename(self.old_name, self.new_name)
            self.finished.emit(True, f'已重命名为 {self.new_name}')
        except Exception as e:
            self.finished.emit(False, str(e))


class DeviceCodeWorker(QThread):
    """获取设备码 + 用户码 + 二维码 URL"""
    finished = Signal(dict, str)  # (response_dict, error)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        try:
            import requests
            cfg = reload_config()
            client_id = cfg['api_config']['client_id']
            url = (
                'https://openapi.baidu.com/oauth/2.0/device/code'
                f'?response_type=device_code&client_id={client_id}&scope=basic,netdisk'
            )
            headers = {'User-Agent': 'pan.baidu.com'}
            resp = requests.get(url, headers=headers, timeout=15).json()
            if 'device_code' in resp:
                self.finished.emit(resp, '')
            else:
                self.finished.emit({}, resp.get('error_description', str(resp)))
        except Exception as e:
            self.finished.emit({}, str(e))


class TokenPollWorker(QThread):
    """轮询用 device_code 换取 access_token"""
    finished = Signal(dict, str)  # (token_dict, error)

    def __init__(self, device_code, client_id, client_secret, parent=None):
        super().__init__(parent)
        self.device_code = device_code
        self.client_id = client_id
        self.client_secret = client_secret

    def run(self):
        try:
            import requests
            url = (
                'https://openapi.baidu.com/oauth/2.0/token'
                f'?grant_type=device_token&code={self.device_code}'
                f'&client_id={self.client_id}&client_secret={self.client_secret}'
            )
            headers = {'User-Agent': 'pan.baidu.com'}
            resp = requests.get(url, headers=headers, timeout=15).json()
            self.finished.emit(resp, '')
        except Exception as e:
            self.finished.emit({}, str(e))


class BuiltinDownloader(QObject):
    """内建多线程下载器 — 从 dlink URL 下载文件到本地"""
    progress = Signal(str, int, int)  # (filename, downloaded_bytes, total_bytes)
    file_done = Signal(str)           # filename — 单文件完成
    all_done = Signal(int)            # total_files — 全部完成

    def __init__(self, links, save_path, threads=5, parent=None):
        super().__init__(parent)
        self.links = links          # [(dlink_url, relative_path), ...]
        self.save_path = save_path
        self.threads = threads
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        import os, requests, threading
        total = len(self.links)

        for i, (url, rel_path) in enumerate(self.links):
            if self._cancelled:
                break
            rel = rel_path.lstrip('/')
            local = os.path.join(self.save_path, rel)
            os.makedirs(os.path.dirname(local) if os.path.dirname(local) else self.save_path, exist_ok=True)

            # 检查断点：已有完整文件则跳过
            if os.path.exists(local):
                existing_size = os.path.getsize(local)
                head = requests.head(url, headers={'User-Agent': 'pan.baidu.com'},
                                     timeout=15, allow_redirects=True)
                remote_size = int(head.headers.get('Content-Length', 0))
                if existing_size == remote_size and remote_size > 0:
                    print(f'[下载] {local} 已存在 ({sizeof_fmt(existing_size)}), 跳过')
                    self.file_done.emit(rel)
                    continue
                else:
                    print(f'[下载] {local} 不完整 (本地 {sizeof_fmt(existing_size)} vs 远程 {sizeof_fmt(remote_size)}), 重新下载')
                    os.remove(local)

            try:
                headers = {'User-Agent': 'pan.baidu.com'}
                head = requests.head(url, headers=headers, timeout=15, allow_redirects=True)
                total_size = int(head.headers.get('Content-Length', 0))
                print(f'[下载] {PurePosixPath(local).name}: {sizeof_fmt(total_size)}')

                if total_size == 0:
                    print(f'[下载单线程] 开始下载 {PurePosixPath(local).name}')
                    self._download_single(url, local, headers, total_size)
                else:
                    self._download_chunked(url, local, headers, total_size)

                self.file_done.emit(rel)
                print(f'[下载] {PurePosixPath(local).name}: 完成')
            except Exception as e:
                print(f'[下载] {PurePosixPath(local).name}: 出错 {e}')
                import traceback; traceback.print_exc()
                try:
                    self._download_single(url, local, {'User-Agent': 'pan.baidu.com'}, 0)
                    self.file_done.emit(rel)
                except Exception:
                    pass

        self.all_done.emit(total)

    def _download_single(self, url, local, headers, total_size):
        import requests
        resp = requests.get(url, headers=headers, stream=True, timeout=60, allow_redirects=True)
        resp.raise_for_status()
        downloaded = 0
        last_report = 0
        REPORT_INTERVAL = 2 * 1024 * 1024  # 每 2MB 汇报一次进度
        print(f'[下载单线程] {PurePosixPath(local).name}: 开始接收数据...')
        with open(local, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=128 * 1024):
                if self._cancelled:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if downloaded - last_report >= REPORT_INTERVAL or downloaded >= total_size:
                    last_report = downloaded
                    print(f'[下载单线程] {PurePosixPath(local).name}: {sizeof_fmt(downloaded)} / {sizeof_fmt(total_size or downloaded)}')
                    self.progress.emit(local, downloaded, total_size or downloaded)

    def _download_chunked(self, url, local, headers, total_size):
        import threading, requests, os, time
        from queue import Queue, Empty

        chunk_size = max(1024 * 1024, total_size // self.threads)
        chunks = []
        for i in range(self.threads):
            start = i * chunk_size
            end = min(start + chunk_size - 1, total_size - 1) if i < self.threads - 1 else total_size - 1
            if start > end:
                continue
            chunks.append((start, end))

        actual_threads = len(chunks)
        print(f'[下载分块] {PurePosixPath(local).name}: {actual_threads} 线程, '
              f'每块 ~{chunk_size / 1024 / 1024:.0f} MB')

        # 验证 Range 支持
        test_h = {**headers, 'Range': 'bytes=0-0'}
        try:
            r_test = requests.get(url, headers=test_h, timeout=15, allow_redirects=False)
            redirect_count = 0
            while r_test.status_code in (301, 302, 303, 307, 308) and redirect_count < 5:
                rloc = r_test.headers.get('Location', '')
                if not rloc:
                    break
                r_test = requests.get(rloc, headers=test_h, timeout=15, allow_redirects=False)
                redirect_count += 1
            range_ok = (r_test.status_code == 206)
        except Exception:
            range_ok = False

        if not range_ok:
            print(f'[下载分块] {PurePosixPath(local).name}: Range 不支持, 降级单线程')
            self._download_single(url, local, headers, total_size)
            return

        progress_per_chunk = [0] * actual_threads
        lock = threading.Lock()
        last_reported = [0]
        REPORT_INTERVAL = 2 * 1024 * 1024
        tmp_files = [f'{local}.part{i}' for i in range(actual_threads)]
        errors = []

        # 线程安全队列：Python 子线程 put，QThread 轮询 get + emit 信号
        progress_queue = Queue()

        def fetch_chunk(idx, start, end):
            if self._cancelled:
                return
            range_header = f'bytes={start}-{end}'
            h = {**headers, 'Range': range_header}
            try:
                r = requests.get(url, headers=h, stream=True, timeout=120, allow_redirects=True)
                if r.status_code == 200:
                    errors.append(f'块{idx}: 服务器返回200(忽略Range)')
                with open(tmp_files[idx], 'wb') as f:
                    for data in r.iter_content(chunk_size=64 * 1024):
                        if self._cancelled:
                            break
                        f.write(data)
                        with lock:
                            progress_per_chunk[idx] += len(data)
                            total_downloaded = sum(progress_per_chunk)
                            if total_downloaded - last_reported[0] >= REPORT_INTERVAL or total_downloaded >= total_size:
                                last_reported[0] = total_downloaded
                                progress_queue.put((local, total_downloaded, total_size))
            except Exception as e:
                errors.append(f'块{idx}: {e}')

        threads_list = []
        for idx, (start, end) in enumerate(chunks):
            t = threading.Thread(target=fetch_chunk, args=(idx, start, end))
            t.daemon = True
            t.start()
            threads_list.append(t)

        # 在 QThread 上下文中轮询进度并安全 emit 信号
        t_start = time.time()
        while any(t.is_alive() for t in threads_list):
            try:
                path, done, total = progress_queue.get(timeout=0.3)
                self.progress.emit(path, done, total)
            except Empty:
                pass

        # 排空剩余进度事件
        while True:
            try:
                path, done, total = progress_queue.get_nowait()
                self.progress.emit(path, done, total)
            except Empty:
                break

        for t in threads_list:
            t.join()

        elapsed = time.time() - t_start
        with lock:
            total_downloaded = sum(progress_per_chunk)

        if errors:
            for e in errors:
                print(f'[下载分块] ⚠️ {e}')

        if not self._cancelled and total_downloaded > 0:
            # 合并分块（流式，不占内存）
            buf_size = 4 * 1024 * 1024
            print(f'[下载分块] 合并中...')
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
                        pass
            # 清理临时文件
            for fname in tmp_files:
                try:
                    os.remove(fname)
                except OSError:
                    pass
            speed = total_downloaded / elapsed if elapsed > 0 else 0
            print(f'[下载分块] {PurePosixPath(local).name}: 完成 '
                  f'({sizeof_fmt(total_downloaded)}, {elapsed:.0f}s, {sizeof_fmt(speed)}/s)')
        elif not self._cancelled:
            print(f'[下载分块] {PurePosixPath(local).name}: 无数据, 尝试单线程回退')
            self._download_single(url, local, headers, total_size)


class UpdatedDownloadWorker(QThread):
    """获取下载链接并根据配置选择内建下载或 aria2"""
    download_finished = Signal(bool, str, int)
    dl_progress = Signal(str, int, int)
    dl_file_done = Signal(str)

    def __init__(self, account_obj, path, is_dir=True, fs_id=None, parent=None):
        super().__init__(parent)
        self.account = account_obj
        self.path = path
        self.is_dir = is_dir
        self.fs_id = fs_id

    def run(self):
        try:
            print(f'[下载] 开始处理: {self.path} ({"文件夹" if self.is_dir else "文件"})')
            self.account.set_extractor()
            if self.is_dir or self.fs_id is None:
                self.account.set_fsids(self.path)
            else:
                print(f'[下载] 文件模式, 直接使用 fsid={self.fs_id}')
                self.account.download_dir = str(PurePosixPath(self.path).parent)
                self.account.extractor.set_fsids([self.fs_id])
            links = self.account.extractor.get_dlink()
            print(f'[下载] 获取到 {len(links) if links else 0} 个下载链接')
            if not links or len(links) == 0:
                self.download_finished.emit(False, '未获取到下载链接（可能路径为空或无权限）', 0)
                return

            cfg = reload_config()
            mode = cfg['download']['mode'] if cfg.has_section('download') else 'aria2'
            print(f'[下载] 模式: {mode}')

            if mode == 'builtin':
                save_path = cfg['download'].get('save_path', './downloads')
                threads = int(cfg['download'].get('threads', '5'))
                print(f'[下载] 保存路径: {save_path}, 线程数: {threads}')
                dl = BuiltinDownloader(links, save_path, threads)
                dl.all_done.connect(
                    lambda total: self.download_finished.emit(True, f'下载完成 ({total} 个文件)', total))
                dl.progress.connect(lambda f, d, t: self.dl_progress.emit(f, d, t))
                dl.file_done.connect(lambda f: self.dl_file_done.emit(f))
                print(f'[下载] 开始调用 BuiltinDownloader.run(), 文件数: {len(links)}')
                dl.run()
                print(f'[下载] BuiltinDownloader.run() 返回')
            else:
                print(f'[下载] 推送到 aria2 ({len(links)} 个任务)')
                aria2.Aria2().add_task(links, self.account.download_dir)
                self.download_finished.emit(True, f'已将 {len(links)} 个下载任务推送到 aria2', len(links))
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.download_finished.emit(False, f'下载异常: {e}', 0)


# ═══════════════════════════════════════════════════════════════════════════
# 下载设置对话框
# ═══════════════════════════════════════════════════════════════════════════

class SettingsDialog(QDialog):
    """下载配置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        self.setWindowTitle('下载设置')
        self.setMinimumSize(500, 460)
        self.resize(500, 460)
        self.setStyleSheet(DIALOG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(14)

        cfg = reload_config()

        # ── 下载模式 ──
        mode_group = QGroupBox('下载模式')
        mg = QVBoxLayout(mode_group)
        mg.setContentsMargins(16, 16, 16, 16)
        mg.setSpacing(10)

        self.radio_builtin = QPushButton('内建下载器（多线程）')
        self.radio_builtin.setCheckable(True)
        self.radio_builtin.setStyleSheet(TOOLBAR_BTN_STYLE)
        self.radio_aria2 = QPushButton('外部 aria2 RPC')
        self.radio_aria2.setCheckable(True)
        self.radio_aria2.setStyleSheet(TOOLBAR_BTN_STYLE)

        # 选中状态样式切换（互斥）
        def on_builtin():
            self.radio_builtin.setChecked(True)
            self.radio_aria2.setChecked(False)
            self.radio_builtin.setStyleSheet(REGULAR_BTN_STYLE)
            self.radio_aria2.setStyleSheet(TOOLBAR_BTN_STYLE)
            self.frame_builtin.setVisible(True)
            self.frame_aria2.setVisible(False)

        def on_aria2():
            self.radio_aria2.setChecked(True)
            self.radio_builtin.setChecked(False)
            self.radio_aria2.setStyleSheet(REGULAR_BTN_STYLE)
            self.radio_builtin.setStyleSheet(TOOLBAR_BTN_STYLE)
            self.frame_builtin.setVisible(False)
            self.frame_aria2.setVisible(True)

        self.radio_builtin.clicked.connect(on_builtin)
        self.radio_aria2.clicked.connect(on_aria2)

        row = QHBoxLayout()
        row.addWidget(self.radio_builtin)
        row.addWidget(self.radio_aria2)
        mg.addLayout(row)
        root.addWidget(mode_group)

        # ── 内建设置 ──
        self.frame_builtin = QFrame()
        fb = QVBoxLayout(self.frame_builtin)
        fb.setSpacing(10)
        fb.setContentsMargins(0, 0, 0, 0)

        # 保存路径
        row1 = QHBoxLayout(); row1.setSpacing(10)
        row1.addWidget(QLabel('保存路径'))
        save_default = cfg['download'].get('save_path', './downloads') if cfg.has_section('download') else './downloads'
        self.edit_save = QLineEdit()
        self.edit_save.setText(save_default)
        self.edit_save.setReadOnly(True)
        self.edit_save.setMinimumHeight(34)
        self.edit_save.setStyleSheet(f'background: {Colors.BG}; color: {Colors.TEXT_SEC};')
        row1.addWidget(self.edit_save)
        btn_save = QPushButton('浏览...')
        btn_save.setStyleSheet(SECONDARY_BTN_STYLE)
        btn_save.setMinimumHeight(34)
        btn_save.clicked.connect(self._browse_save_path)
        row1.addWidget(btn_save)
        fb.addLayout(row1)

        # 缓存路径
        row2 = QHBoxLayout(); row2.setSpacing(10)
        row2.addWidget(QLabel('缓存路径'))
        cache_default = cfg['download'].get('cache_path', './cache') if cfg.has_section('download') else './cache'
        self.edit_cache = QLineEdit()
        self.edit_cache.setText(cache_default)
        self.edit_cache.setReadOnly(True)
        self.edit_cache.setMinimumHeight(34)
        self.edit_cache.setStyleSheet(f'background: {Colors.BG}; color: {Colors.TEXT_SEC};')
        row2.addWidget(self.edit_cache)
        btn_cache = QPushButton('浏览...')
        btn_cache.setStyleSheet(SECONDARY_BTN_STYLE)
        btn_cache.setMinimumHeight(34)
        btn_cache.clicked.connect(self._browse_cache_path)
        row2.addWidget(btn_cache)
        fb.addLayout(row2)

        # 线程数
        row3 = QHBoxLayout(); row3.setSpacing(10)
        row3.addWidget(QLabel('线程数量'))
        self.combo_threads = QComboBox()
        self.combo_threads.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        current_threads = cfg['download'].get('threads', '5') if cfg.has_section('download') else '5'
        idx = self.combo_threads.findText(current_threads)
        if idx >= 0:
            self.combo_threads.setCurrentIndex(idx)
        self.combo_threads.setMinimumHeight(34)
        row3.addWidget(self.combo_threads)
        row3.addStretch()
        fb.addLayout(row3)

        root.addWidget(self.frame_builtin)

        # ── aria2 设置 ──
        self.frame_aria2 = QFrame()
        fa = QVBoxLayout(self.frame_aria2)
        fa.setSpacing(10)
        fa.setContentsMargins(0, 0, 0, 0)

        # 协议
        row_p = QHBoxLayout(); row_p.setSpacing(10)
        self.radio_http = QPushButton('HTTP')
        self.radio_http.setCheckable(True)
        self.radio_http.setStyleSheet(TOOLBAR_BTN_STYLE)
        self.radio_https = QPushButton('HTTPS')
        self.radio_https.setCheckable(True)
        self.radio_https.setStyleSheet(TOOLBAR_BTN_STYLE)

        aria_schema = cfg['aria2'].get('schema', 'http')
        if aria_schema == 'https':
            self.radio_https.setChecked(True)
            self.radio_https.setStyleSheet(REGULAR_BTN_STYLE)
        else:
            self.radio_http.setChecked(True)
            self.radio_http.setStyleSheet(REGULAR_BTN_STYLE)

        # 互斥切换
        def on_http():
            self.radio_http.setChecked(True)
            self.radio_https.setChecked(False)
            self.radio_http.setStyleSheet(REGULAR_BTN_STYLE)
            self.radio_https.setStyleSheet(TOOLBAR_BTN_STYLE)

        def on_https():
            self.radio_https.setChecked(True)
            self.radio_http.setChecked(False)
            self.radio_https.setStyleSheet(REGULAR_BTN_STYLE)
            self.radio_http.setStyleSheet(TOOLBAR_BTN_STYLE)

        self.radio_http.clicked.connect(on_http)
        self.radio_https.clicked.connect(on_https)

        row_p.addWidget(QLabel('协议'))
        row_p.addWidget(self.radio_http)
        row_p.addWidget(self.radio_https)
        row_p.addStretch()
        fa.addLayout(row_p)

        # 地址
        row_a = QHBoxLayout(); row_a.setSpacing(10)
        row_a.addWidget(QLabel('地址'))
        self.edit_addr = QLineEdit()
        self.edit_addr.setText(cfg['aria2'].get('rpc', ''))
        self.edit_addr.setMinimumHeight(34)
        row_a.addWidget(self.edit_addr)
        fa.addLayout(row_a)

        # 端口
        row_b = QHBoxLayout(); row_b.setSpacing(10)
        row_b.addWidget(QLabel('端口'))
        self.edit_port = QLineEdit()
        self.edit_port.setText(cfg['aria2'].get('port', '6800'))
        self.edit_port.setMinimumHeight(34)
        row_b.addWidget(self.edit_port)
        fa.addLayout(row_b)

        # 密钥
        row_c = QHBoxLayout(); row_c.setSpacing(10)
        row_c.addWidget(QLabel('密钥'))
        self.edit_secret = QLineEdit()
        self.edit_secret.setText(cfg['aria2'].get('secret', ''))
        self.edit_secret.setPlaceholderText('留空表示无密钥')
        self.edit_secret.setMinimumHeight(34)
        row_c.addWidget(self.edit_secret)
        fa.addLayout(row_c)

        root.addWidget(self.frame_aria2)

        # 初始状态
        mode = cfg['download'].get('mode', 'aria2') if cfg.has_section('download') else 'aria2'
        if mode == 'builtin':
            self.radio_builtin.setChecked(True)
            self.radio_builtin.setStyleSheet(REGULAR_BTN_STYLE)
            self.radio_aria2.setStyleSheet(TOOLBAR_BTN_STYLE)
            self.frame_builtin.setVisible(True)
            self.frame_aria2.setVisible(False)
        else:
            self.radio_aria2.setChecked(True)
            self.radio_aria2.setStyleSheet(REGULAR_BTN_STYLE)
            self.radio_builtin.setStyleSheet(TOOLBAR_BTN_STYLE)
            self.frame_builtin.setVisible(False)
            self.frame_aria2.setVisible(True)

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()
        btn_cancel = QPushButton('取消')
        btn_cancel.setStyleSheet(SECONDARY_BTN_STYLE)
        btn_cancel.setMinimumHeight(38)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        btn_save = QPushButton('保存')
        btn_save.setStyleSheet(REGULAR_BTN_STYLE)
        btn_save.setMinimumHeight(38)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)
        root.addLayout(btn_row)

    def _browse_save_path(self):
        path = QFileDialog.getExistingDirectory(self, '选择文件保存路径',
                                                 self.edit_save.text())
        if path:
            self.edit_save.setText(path)

    def _browse_cache_path(self):
        path = QFileDialog.getExistingDirectory(self, '选择缓存路径',
                                                 self.edit_cache.text())
        if path:
            self.edit_cache.setText(path)

    def _save(self):
        cfg = reload_config()
        # Download section
        if not cfg.has_section('download'):
            cfg.add_section('download')
        cfg.set('download', 'mode', 'builtin' if self.radio_builtin.isChecked() else 'aria2')
        cfg.set('download', 'save_path', self.edit_save.text().strip() or './downloads')
        cfg.set('download', 'cache_path', self.edit_cache.text().strip() or './cache')
        cfg.set('download', 'threads', self.combo_threads.currentText())

        # Aria2 section
        if not cfg.has_section('aria2'):
            cfg.add_section('aria2')
        cfg.set('aria2', 'schema', 'https' if self.radio_https.isChecked() else 'http')
        cfg.set('aria2', 'rpc', self.edit_addr.text().strip())
        cfg.set('aria2', 'port', self.edit_port.text().strip() or '6800')
        cfg.set('aria2', 'secret', self.edit_secret.text().strip())

        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            cfg.write(f)

        QMessageBox.information(self, '已保存', '下载设置已保存')
        self.accept()


# ═══════════════════════════════════════════════════════════════════════════
# 下载管理器对话框
# ═══════════════════════════════════════════════════════════════════════════

class DownloadManager(QDialog):
    """下载进度管理 — 可关闭在后台运行，完成后状态栏通知"""

    all_done = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tasks = []         # [(path, label, widget), ...]
        self._active_dl = None   # BuiltinDownloader 引用
        self._done_emitted = False
        self._build()

    def _build(self):
        self.setWindowTitle('下载管理')
        self.setMinimumSize(520, 320)
        self.resize(520, 400)
        self.setStyleSheet(DIALOG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(0)

        # 标题栏
        title_bar = QHBoxLayout()
        lbl = QLabel('下载任务')
        lbl.setStyleSheet(f'font-size: 16px; font-weight: 700; color: {Colors.TEXT};')
        title_bar.addWidget(lbl)
        title_bar.addStretch()
        self.lbl_summary = QLabel('')
        self.lbl_summary.setStyleSheet(f'font-size: 12px; color: {Colors.TEXT_SEC};')
        title_bar.addWidget(self.lbl_summary)
        root.addLayout(title_bar)
        root.addSpacing(8)

        # 任务列表（可滚动）
        scroll_area = QFrame()
        scroll_layout = QVBoxLayout(scroll_area)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(6)
        self.task_container = QVBoxLayout()
        scroll_layout.addLayout(self.task_container)
        scroll_layout.addStretch()
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setWidget(scroll_area)
        sa.setStyleSheet(f'QScrollArea {{ border: none; background: {Colors.BG_CARD}; }}')
        root.addWidget(sa, 1)

        # 底部按钮
        root.addSpacing(10)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_close = QPushButton('关闭（后台继续）')
        self.btn_close.setStyleSheet(SECONDARY_BTN_STYLE)
        self.btn_close.setMinimumHeight(36)
        self.btn_close.clicked.connect(self._hide_to_tray)
        btn_row.addWidget(self.btn_close)
        root.addLayout(btn_row)

    def add_task(self, path, label=''):
        """添加一个下载任务条目，返回 QFrame widget"""
        self._done_emitted = False
        display = label or PurePosixPath(path).name
        frame = QFrame()
        frame.setStyleSheet(f'''
            QFrame {{
                background: {Colors.BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 10px;
            }}
        ''')
        f_layout = QVBoxLayout(frame)
        f_layout.setSpacing(6)
        f_layout.setContentsMargins(12, 10, 12, 10)

        # 第一行：文件名 + 状态
        top = QHBoxLayout()
        name_lbl = QLabel(display)
        name_lbl.setStyleSheet(f'font-size: 13px; font-weight: 500; color: {Colors.TEXT};')
        name_lbl.setWordWrap(True)
        top.addWidget(name_lbl, 1)
        status_lbl = QLabel('等待中')
        status_lbl.setStyleSheet(f'font-size: 12px; color: {Colors.TEXT_SEC};')
        top.addWidget(status_lbl)
        f_layout.addLayout(top)

        # 进度条
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        f_layout.addWidget(bar)

        # 详情
        detail_lbl = QLabel('')
        detail_lbl.setStyleSheet(f'font-size: 11px; color: {Colors.TEXT_DIM};')
        f_layout.addWidget(detail_lbl)

        self.task_container.addWidget(frame)
        info = {
            'frame': frame, 'bar': bar, 'status': status_lbl,
            'detail': detail_lbl, 'path': path, 'name': name_lbl
        }
        self._tasks.append(info)
        self._update_summary()
        return info

    def update_task(self, info, status, progress=None, detail=''):
        info['status'].setText(status)
        if info['status'].text() == '完成':
            info['status'].setStyleSheet(f'font-size: 12px; color: {Colors.GREEN_TEXT};')
        elif '失败' in status:
            info['status'].setStyleSheet(f'font-size: 12px; color: {Colors.DANGER};')
        if progress is not None:
            info['bar'].setValue(progress)
        if detail:
            info['detail'].setText(detail)
        self._update_summary()

    def _update_summary(self):
        done = sum(1 for t in self._tasks if t['status'].text() == '完成')
        fail = sum(1 for t in self._tasks if '失败' in t['status'].text())
        total = len(self._tasks)
        self.lbl_summary.setText(f'{done}/{total} 完成' + (f'  {fail} 失败' if fail else ''))

        if done + fail >= total and total > 0 and not self._done_emitted:
            self._done_emitted = True
            self.btn_close.setText('关闭')
            self.btn_close.setStyleSheet(REGULAR_BTN_STYLE)
            self.all_done.emit()

    def set_active_downloader(self, dl):
        self._active_dl = dl

    def _hide_to_tray(self):
        """关闭窗口但不停止下载（已有任务继续）"""
        self.hide()

    def reject(self):
        """点 × 时隐藏而非关闭"""
        self._hide_to_tray()


# ═══════════════════════════════════════════════════════════════════════════
# 登录对话框
# ═══════════════════════════════════════════════════════════════════════════

class LoginDialog(QDialog):
    """设备码模式登录对话框 — 二维码扫码授权"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.account_obj = None
        self._device_code = None
        self._user_code = None
        self._client_id = None
        self._client_secret = None
        self._poll_timer = None
        self._poll_count = 0
        self._max_polls = 60  # 5分钟 / 5秒
        self._build()

    def _build(self):
        self.setWindowTitle('登录 — 百度网盘')
        self.setMinimumSize(580, 620)
        self.resize(580, 620)
        self.setStyleSheet(DIALOG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(16)

        # Header
        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        self._avatar_label = QLabel()
        self._avatar_label.setFixedSize(44, 44)
        self._avatar_label.setStyleSheet(f"""
            QLabel {{
                background: {Colors.ACCENT_BG};
                border: 2px solid {Colors.ACCENT};
                border-radius: 22px;
                font-size: 20px;
                font-weight: bold;
                color: {Colors.ACCENT};
                qproperty-alignment: AlignCenter;
            }}
        """)
        self._avatar_label.setText('☁')
        header_row.addWidget(self._avatar_label)
        header_title = QLabel('百度网盘')
        header_title.setStyleSheet(f'font-size: 22px; font-weight: 700; color: {Colors.TEXT};')
        header_row.addWidget(header_title)
        header_row.addStretch()
        root.addLayout(header_row)

        # ── 已有账户 ──
        existing_group = QGroupBox('已有账户')
        existing_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        eg = QVBoxLayout(existing_group)
        eg.setSpacing(10)
        eg.setContentsMargins(16, 16, 16, 16)
        self.combo_accounts = QComboBox()
        self.combo_accounts.setMinimumHeight(34)
        eg.addWidget(self.combo_accounts)
        self.btn_use = QPushButton('使用选中账户')
        self.btn_use.setStyleSheet(REGULAR_BTN_STYLE)
        self.btn_use.setMinimumHeight(38)
        self.btn_use.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_use.clicked.connect(self._use_existing)
        eg.addWidget(self.btn_use)
        root.addWidget(existing_group)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f'background: {Colors.BORDER}; max-height: 1px; border: none;')
        root.addWidget(div)

        # ── 添加新账户（设备码模式） ──
        new_group = QGroupBox('扫码添加新账户')
        new_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        ng = QVBoxLayout(new_group)
        ng.setSpacing(12)
        ng.setContentsMargins(16, 16, 16, 16)

        # 账户名 + 获取按钮
        name_row = QHBoxLayout()
        name_row.setSpacing(10)
        name_lbl = QLabel('名称')
        name_lbl.setStyleSheet(f'font-weight: 500; color: {Colors.TEXT_SEC}; min-width: 48px;')
        name_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        name_row.addWidget(name_lbl)
        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText('为此账户起个名，如 main')
        self.edit_name.setMinimumHeight(34)
        name_row.addWidget(self.edit_name)
        self.btn_get_code = QPushButton('获取二维码')
        self.btn_get_code.setStyleSheet(REGULAR_BTN_STYLE)
        self.btn_get_code.setMinimumHeight(34)
        self.btn_get_code.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_get_code.clicked.connect(self._start_device_auth)
        name_row.addWidget(self.btn_get_code)
        ng.addLayout(name_row)

        # 二维码显示区域
        qr_frame = QFrame()
        qr_frame.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG};
                border: 2px dashed {Colors.BORDER};
                border-radius: 10px;
            }}
        """)
        qr_frame.setFixedHeight(200)
        qr_layout = QVBoxLayout(qr_frame)
        qr_layout.setAlignment(Qt.AlignCenter)

        self.lbl_qr = QLabel()
        self.lbl_qr.setFixedSize(160, 160)
        self.lbl_qr.setAlignment(Qt.AlignCenter)
        self.lbl_qr.setStyleSheet(f"""
            QLabel {{
                border: none;
                font-size: 12px;
                color: {Colors.TEXT_DIM};
            }}
        """)
        self.lbl_qr.setText('等待获取\n二维码...')
        qr_layout.addWidget(self.lbl_qr, alignment=Qt.AlignCenter)
        ng.addWidget(qr_frame)

        # 状态 + 用户码
        status_row = QHBoxLayout()
        self.lbl_status = QLabel('请先输入账户名称并点击"获取二维码"')
        self.lbl_status.setStyleSheet(f'font-size: 12px; color: {Colors.TEXT_SEC};')
        self.lbl_status.setWordWrap(True)
        status_row.addWidget(self.lbl_status, 1)

        self.lbl_user_code = QLabel('')
        self.lbl_user_code.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 700;
                color: {Colors.ACCENT};
                background: {Colors.ACCENT_BG};
                border: 1px solid {Colors.ACCENT_BORDER};
                border-radius: 6px;
                padding: 4px 14px;
            }}
        """)
        self.lbl_user_code.setVisible(False)
        status_row.addWidget(self.lbl_user_code)
        ng.addLayout(status_row)

        # 倒计时
        self.lbl_countdown = QLabel('')
        self.lbl_countdown.setStyleSheet(f'font-size: 11px; color: {Colors.TEXT_DIM};')
        self.lbl_countdown.setAlignment(Qt.AlignCenter)
        self.lbl_countdown.setVisible(False)
        ng.addWidget(self.lbl_countdown)

        root.addWidget(new_group)

        self._refresh_account_list()

    # ── 现有账户 ────────────────────────────────────────────────────────

    def _refresh_account_list(self):
        self.combo_accounts.clear()
        names = get_account_names()
        for name in names:
            self.combo_accounts.addItem(name)
        if not names:
            self.combo_accounts.addItem('（无已保存账户）')
            self.btn_use.setEnabled(False)
        else:
            self.btn_use.setEnabled(True)

    def _use_existing(self):
        name = self.combo_accounts.currentText()
        if '（无' in name:
            return

        # 禁用按钮，异步验证
        self.btn_use.setEnabled(False)
        self.btn_use.setText('验证中...')

        self._verify_worker = VerifyAccountWorker(name)
        self._verify_worker.finished.connect(self._on_verify_done)
        self._verify_worker.start()

    def _on_verify_done(self, acc, error):
        self.btn_use.setEnabled(True)
        self.btn_use.setText('使用选中账户')

        if acc is not None:
            self.account_obj = acc
            self.accept()
        else:
            QMessageBox.critical(self, '错误', f'加载账户失败：{error}')

    # ── 设备码授权 ──────────────────────────────────────────────────────

    def _start_device_auth(self):
        name = self.edit_name.text().strip()
        if not name:
            return QMessageBox.warning(self, '请输入', '请输入账户名称')
        if name in ('api_config', 'aria2'):
            return QMessageBox.warning(self, '保留名', '该名称为保留名称，请换用其他名称')

        # 检查 API 配置
        cfg = reload_config()
        try:
            self._client_id = cfg['api_config']['client_id'].strip()
            self._client_secret = cfg['api_config']['client_secret'].strip()
        except KeyError:
            return QMessageBox.critical(self, '配置错误', 'config.ini 中缺少 api_config 配置')

        if not self._client_id:
            return QMessageBox.critical(self, '配置错误',
                'config.ini 中 client_id 为空\n请在百度开发者控制台获取 AppKey 并填入')

        # 禁用按钮，开始获取设备码
        self.btn_get_code.setEnabled(False)
        self.btn_get_code.setText('获取中...')
        self.lbl_status.setText('正在获取设备码...')
        self.lbl_qr.setText('⏳')
        self.lbl_qr.setStyleSheet(f'border: none; font-size: 32px; color: {Colors.TEXT_DIM};')
        self.lbl_user_code.setVisible(False)
        self.lbl_countdown.setVisible(False)

        self._worker_code = DeviceCodeWorker()
        self._worker_code.finished.connect(self._on_device_code_ready)
        self._worker_code.start()

    def _on_device_code_ready(self, resp, error):
        self.btn_get_code.setText('获取二维码')
        self.btn_get_code.setEnabled(True)

        if error or not resp:
            self.lbl_status.setText(f'获取失败：{error}')
            self.lbl_qr.setText('❌')
            return

        self._device_code = resp['device_code']
        self._user_code = resp['user_code']
        qrcode_url = resp.get('qrcode_url', '')

        # 展示用户码
        self.lbl_user_code.setText(self._user_code)
        self.lbl_user_code.setVisible(True)

        # 加载二维码图片
        if qrcode_url:
            self._load_qr_image(qrcode_url)
        else:
            # 备用：用 API 拼接 URL
            url_base = resp.get('verification_url', 'https://openapi.baidu.com/device')
            alt_url = f'{url_base}?display=mobile&code={self._user_code}'
            self.lbl_qr.setText(f'扫码地址：\n{alt_url[:60]}...')
            self.lbl_qr.setStyleSheet(f'border: none; font-size: 10px; color: {Colors.TEXT_SEC}; padding: 8px;')

        self.lbl_status.setText(f'请使用百度 App 扫描二维码完成授权')
        self.lbl_countdown.setText(f'有效期 {resp.get("expires_in", 300)} 秒')
        self.lbl_countdown.setVisible(True)

        # 启动轮询
        self._poll_count = 0
        self._start_polling()

    def _load_qr_image(self, url):
        """异步加载二维码图片"""
        class QrLoader(QThread):
            loaded = Signal(object)  # QPixmap or None
            def run(self):
                try:
                    import requests
                    r = requests.get(url, timeout=10)
                    if r.status_code == 200:
                        pix = QPixmap()
                        pix.loadFromData(r.content)
                        self.loaded.emit(pix)
                    else:
                        self.loaded.emit(None)
                except Exception:
                    self.loaded.emit(None)

        self._qr_loader = QrLoader()
        self._qr_loader.loaded.connect(self._on_qr_loaded)
        self._qr_loader.start()

    def _on_qr_loaded(self, pixmap):
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_qr.setPixmap(scaled)
            self.lbl_qr.setStyleSheet('border: none;')
        else:
            self.lbl_qr.setText('二维码加载失败\n请使用下方用户码授权')
            self.lbl_qr.setStyleSheet(f'border: none; font-size: 11px; color: {Colors.DANGER}; padding: 8px;')

    # ── Token 轮询 ──────────────────────────────────────────────────────

    def _start_polling(self):
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_token)
        self._poll_timer.start(5000)  # 每 5 秒轮询

    def _poll_token(self):
        self._poll_count += 1
        remaining = max(0, self._max_polls - self._poll_count)
        self.lbl_countdown.setText(f'已等待 {self._poll_count * 5} 秒  ·  剩余约 {remaining * 5} 秒')

        if self._poll_count > self._max_polls:
            self._stop_polling()
            self.lbl_status.setText('设备码已过期，请重新获取')
            self.lbl_qr.setText('⏰')
            return

        self.worker_poll = TokenPollWorker(
            self._device_code, self._client_id, self._client_secret
        )
        self.worker_poll.finished.connect(self._on_token_result)
        self.worker_poll.start()

    def _on_token_result(self, resp, error):
        if error:
            return  # 网络错误，继续轮询

        if 'access_token' in resp:
            # 授权成功！
            self._stop_polling()
            self.lbl_status.setText('授权成功！正在保存...')
            self._save_new_account(resp)
        elif resp.get('error') == 'authorization_pending':
            self.lbl_status.setText('等待扫码授权中...')
        elif resp.get('error') == 'authorization_declined':
            self._stop_polling()
            self.lbl_status.setText('用户拒绝授权')
            self.lbl_qr.setText('🚫')
        elif resp.get('error') == 'expired_token':
            self._stop_polling()
            self.lbl_status.setText('设备码已过期，请重新获取')
            self.lbl_qr.setText('⏰')
        else:
            self.lbl_status.setText(f'未知错误：{resp.get("error_description", str(resp))}')

    def _stop_polling(self):
        if self._poll_timer:
            self._poll_timer.stop()
            self._poll_timer = None

    def _save_new_account(self, token_resp):
        name = self.edit_name.text().strip()
        try:
            acc = acct.Account(name)
            acc.set_account_info(
                token_resp['access_token'],
                token_resp['refresh_token'],
                token_resp.get('scope', 'basic netdisk')
            )
            acc.save_account_info()
            if acc.check_access_token(0):
                self.account_obj = acc
                self.accept()
            else:
                QMessageBox.warning(self, '验证失败', 'Token 保存后验证失败，请重试')
                self.lbl_status.setText('验证失败，请重试')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存账户失败：{e}')
            self.lbl_status.setText(f'保存失败：{e}')

    def closeEvent(self, event):
        self._stop_polling()
        super().closeEvent(event)


# ═══════════════════════════════════════════════════════════════════════════
# 用户头像组件（纯 QPainter 绘制）
# ═══════════════════════════════════════════════════════════════════════════

class AvatarBadge(QLabel):
    """圆形头像气泡 — 用账户名首字符 + 渐变底色"""

    def __init__(self, text='', size=36, parent=None):
        super().__init__(parent)
        self._text = text[:1].upper() if text else '?'
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        if self._size <= 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRect(0, 0, self._size, self._size)

        # 渐变底色
        grad = QLinearGradient(0, 0, self._size, self._size)
        grad.setColorAt(0, QColor(5, 150, 105))
        grad.setColorAt(1, QColor(16, 185, 129))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(rect, self._size / 2, self._size / 2)

        # 文字
        p.setPen(QColor(Colors.WHITE))
        font = QFont()
        font_size = max(1, int(self._size * 0.45))
        font.setPixelSize(font_size)
        font.setBold(True)
        p.setFont(font)
        p.drawText(rect, Qt.AlignCenter, self._text)
        p.end()


# ═══════════════════════════════════════════════════════════════════════════
# 面包屑导航
# ═══════════════════════════════════════════════════════════════════════════

class BreadcrumbBar(QFrame):
    """可点击面包屑路径导航"""
    segment_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('breadcrumb')
        self.setStyleSheet(f"""
            QFrame#breadcrumb {{
                background: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 6px 0px;
            }}
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 13px;
                color: {Colors.TEXT_SEC};
            }}
            QPushButton:hover {{
                background: {Colors.ACCENT_BG};
                color: {Colors.ACCENT};
            }}
            QPushButton:last {{
                color: {Colors.TEXT};
                font-weight: 600;
            }}
            QLabel {{
                color: {Colors.TEXT_DIM};
                font-size: 13px;
                padding: 0 2px;
            }}
        """)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(10, 4, 10, 4)
        self._layout.setSpacing(0)

    def set_path(self, path: str):
        # 清空旧控件
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        root_btn = QPushButton('根目录')
        root_btn.clicked.connect(lambda: self.segment_clicked.emit('/'))
        self._layout.addWidget(root_btn)

        if path != '/':
            parts = PurePosixPath(path).parts[1:]
            for i, part in enumerate(parts):
                sep = QLabel('›')
                self._layout.addWidget(sep)
                btn = QPushButton(part)
                full = '/' + '/'.join(parts[:i + 1])
                btn.clicked.connect(lambda checked, p=full: self.segment_clicked.emit(p))
                self._layout.addWidget(btn)

        self._layout.addStretch()


# ═══════════════════════════════════════════════════════════════════════════
# 头部面板
# ═══════════════════════════════════════════════════════════════════════════

class HeaderPanel(QFrame):

    logout_requested = Signal()
    switch_requested = Signal()
    refresh_requested = Signal()
    settings_requested = Signal()

    def __init__(self, account_name='', parent=None):
        super().__init__(parent)
        self.setObjectName('header')
        self.setStyleSheet(f"""
            QFrame#header {{
                background: {Colors.BG_HEADER};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        # 头像
        self.avatar = AvatarBadge(account_name, 34)
        layout.addWidget(self.avatar)

        # 账户信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(1)
        self.lbl_account = QLabel(account_name)
        self.lbl_account.setStyleSheet(f'font-size: 14px; font-weight: 600; color: {Colors.TEXT};')
        info_layout.addWidget(self.lbl_account)
        self.lbl_status = QLabel('已连接')
        self.lbl_status.setStyleSheet(f'font-size: 11px; color: {Colors.ACCENT};')
        info_layout.addWidget(self.lbl_status)
        layout.addLayout(info_layout)

        layout.addStretch()

        # 右侧操作
        btn_settings = QPushButton('设置')
        btn_settings.setStyleSheet(TOOLBAR_BTN_STYLE)
        btn_settings.clicked.connect(self.settings_requested.emit)
        layout.addWidget(btn_settings)

        btn_switch = QPushButton('切换')
        btn_switch.setStyleSheet(TOOLBAR_BTN_STYLE)
        btn_switch.clicked.connect(self.switch_requested.emit)
        layout.addWidget(btn_switch)

        btn_refresh = QPushButton('刷新 Token')
        btn_refresh.setStyleSheet(TOOLBAR_BTN_STYLE)
        btn_refresh.clicked.connect(self.refresh_requested.emit)
        layout.addWidget(btn_refresh)

        btn_logout = QPushButton('注销')
        btn_logout.setStyleSheet(TOOLBAR_BTN_STYLE)
        btn_logout.clicked.connect(self.logout_requested.emit)
        layout.addWidget(btn_logout)


# ═══════════════════════════════════════════════════════════════════════════
# 主窗口
# ═══════════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):

    def __init__(self, account_obj):
        super().__init__()
        self.account = account_obj
        self._history = []
        self._history_pos = -1
        self._current_files = []
        self._loading = False
        self._workers = []     # 保持所有活动 worker 引用，防止 GC 回收导致崩溃
        self._build()
        self._refresh_file_list()

    def _safe_start(self, worker):
        """启动 worker 并保持引用防止 GC 回收"""
        self._workers.append(worker)
        worker.finished.connect(lambda *a: self._cleanup_worker(worker))
        worker.start()

    def _cleanup_worker(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)

    # ── UI 构建 ──────────────────────────────────────────────────────────

    def _build(self):
        self.setWindowTitle(f'baidu-linux — {self.account.name}')
        self.resize(1020, 660)
        self.setMinimumSize(700, 400)
        self.setStyleSheet(GLOBAL_STYLE)

        self._create_header()
        self._create_toolbar()
        self._create_breadcrumb()
        self._create_table()
        self._create_status_bar()

        # 主布局
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.breadcrumb_box)
        layout.addWidget(self.table, 1)

    def _create_header(self):
        self.header = HeaderPanel(self.account.name)
        self.header.logout_requested.connect(self._logout)
        self.header.switch_requested.connect(self._switch_account)
        self.header.refresh_requested.connect(self._refresh_token)
        self.header.settings_requested.connect(self._open_settings)

    def _create_toolbar(self):
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)

        btn_back = QPushButton('← 返回')
        btn_back.setStyleSheet(TOOLBAR_BTN_STYLE)
        btn_back.clicked.connect(self._go_back)
        self.toolbar.addWidget(btn_back)

        btn_fwd = QPushButton('前进 →')
        btn_fwd.setStyleSheet(TOOLBAR_BTN_STYLE)
        btn_fwd.clicked.connect(self._go_forward)
        self.toolbar.addWidget(btn_fwd)

        btn_home = QPushButton('根目录')
        btn_home.setStyleSheet(TOOLBAR_BTN_STYLE)
        btn_home.clicked.connect(lambda: self._navigate_to('/'))
        self.toolbar.addWidget(btn_home)

        btn_reload = QPushButton('刷新')
        btn_reload.setStyleSheet(TOOLBAR_BTN_STYLE)
        btn_reload.clicked.connect(self._refresh_file_list)
        self.toolbar.addWidget(btn_reload)

        self.toolbar.addSeparator()

        self.btn_dl = QPushButton('下载')
        self.btn_dl.setStyleSheet(TOOLBAR_BTN_PRIMARY_STYLE)
        self.btn_dl.clicked.connect(self._download_selected)
        self.toolbar.addWidget(self.btn_dl)

        self.btn_del = QPushButton('删除')
        self.btn_del.setStyleSheet(TOOLBAR_BTN_DANGER_STYLE)
        self.btn_del.clicked.connect(self._delete_selected)
        self.toolbar.addWidget(self.btn_del)

        self.btn_rename = QPushButton('重命名')
        self.btn_rename.setStyleSheet(TOOLBAR_BTN_STYLE)
        self.btn_rename.clicked.connect(self._rename_selected)
        self.toolbar.addWidget(self.btn_rename)

        self.toolbar.addSeparator()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedWidth(120)
        self.progress_bar.setVisible(False)
        self.toolbar.addWidget(self.progress_bar)

        # 下载管理入口（始终可见）
        self.btn_dl_mgr = QPushButton('⏬ 下载管理')
        self.btn_dl_mgr.setStyleSheet(TOOLBAR_BTN_STYLE)
        self.btn_dl_mgr.clicked.connect(self._show_download_manager)
        self.toolbar.addWidget(self.btn_dl_mgr)

        self.addToolBar(self.toolbar)

    def _create_breadcrumb(self):
        self.breadcrumb_box = QFrame()
        self.breadcrumb_box.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG};
                padding: 6px 10px;
            }}
        """)
        box_layout = QHBoxLayout(self.breadcrumb_box)
        box_layout.setContentsMargins(0, 0, 0, 0)
        self.breadcrumb = BreadcrumbBar()
        self.breadcrumb.segment_clicked.connect(self._navigate_to)
        box_layout.addWidget(self.breadcrumb)

    def _create_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['名称', '类型', '大小', '修改时间'])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 72)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 150)
        self.table.setAlternatingRowColors(True)
        self.table.cellDoubleClicked.connect(self._on_item_double_clicked)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

    def _create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status()

    # ── 导航 ────────────────────────────────────────────────────────────

    def _navigate_to(self, path, add_history=True):
        if self._loading:
            return
        if add_history and self.account.current_dir != path:
            self._history = self._history[:self._history_pos + 1]
            self._history.append(path)
            self._history_pos = len(self._history) - 1
        self.account.current_dir = path
        self.breadcrumb.set_path(path)
        self._refresh_file_list()
        self._update_status()

    def _go_back(self):
        if self._history_pos > 0:
            self._history_pos -= 1
            path = self._history[self._history_pos]
            self.account.current_dir = path
            self.breadcrumb.set_path(path)
            self._refresh_file_list()
            self._update_status()

    def _go_forward(self):
        if self._history_pos < len(self._history) - 1:
            self._history_pos += 1
            path = self._history[self._history_pos]
            self.account.current_dir = path
            self.breadcrumb.set_path(path)
            self._refresh_file_list()
            self._update_status()

    def _on_item_double_clicked(self, row, col):
        item = self.table.item(row, 0)
        if item is None:
            return
        info = item.data(Qt.UserRole)
        if info and info.get('isdir') == 1:
            self._navigate_to(info['path'])

    # ── 文件列表 ────────────────────────────────────────────────────────

    def _refresh_file_list(self):
        self._set_loading(True)
        self.table.setRowCount(0)
        self._current_files = []
        self.worker_list = ListFilesWorker(self.account, self.account.current_dir)
        self.worker_list.finished.connect(self._on_list_finished)
        self._safe_start(self.worker_list)

    def _set_loading(self, loading):
        self._loading = loading
        self.progress_bar.setVisible(loading)

    def _on_list_finished(self, file_list, error):
        self._set_loading(False)
        if error:
            self._show_error('加载失败', f'无法获取文件列表：{error}')
            return
        self._current_files = file_list
        self._populate_table(file_list)
        self._update_status()

    def _populate_table(self, file_list):
        # 文件夹在前
        dirs = [f for f in file_list if f.get('isdir') == 1]
        files = [f for f in file_list if f.get('isdir') != 1]
        sorted_list = dirs + files
        self.table.setRowCount(len(sorted_list))

        for row, item in enumerate(sorted_list):
            is_dir = item.get('isdir') == 1
            fname = item.get('server_filename', item.get('path', ''))

            # 名称列
            icon = '📁' if is_dir else '📄'
            name_item = QTableWidgetItem(f'  {icon}  {fname}')
            name_item.setData(Qt.UserRole, item)
            font = name_item.font()
            font.setBold(is_dir)
            name_item.setFont(font)
            name_item.setForeground(QColor(Colors.FOLDER if is_dir else Colors.TEXT))
            self.table.setItem(row, 0, name_item)

            # 类型
            ftype = '文件夹' if is_dir else '文件'
            type_item = QTableWidgetItem(ftype)
            type_item.setForeground(QColor(Colors.TEXT_SEC))
            type_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, type_item)

            # 大小
            if is_dir:
                size_str = '—'
            else:
                size_str = sizeof_fmt(item.get('size', 0))
            size_item = QTableWidgetItem(size_str)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            size_item.setForeground(QColor(Colors.TEXT_SEC))
            self.table.setItem(row, 2, size_item)

            # 时间
            mtime = item.get('server_mtime', item.get('local_mtime', ''))
            if mtime and mtime != 0:
                dt = datetime.fromtimestamp(mtime)
                time_str = dt.strftime('%Y-%m-%d  %H:%M')
            else:
                time_str = '—'
            time_item = QTableWidgetItem(time_str)
            time_item.setForeground(QColor(Colors.TEXT_DIM))
            self.table.setItem(row, 3, time_item)

        # 更新状态栏计数
        self._update_status(dir_count=len(dirs), file_count=len(files))

    # ── 状态栏 ──────────────────────────────────────────────────────────

    def _update_status(self, dir_count=None, file_count=None):
        if dir_count is None:
            dir_count = len([f for f in self._current_files if f.get('isdir') == 1])
        if file_count is None:
            file_count = len([f for f in self._current_files if f.get('isdir') != 1])
        self.status_bar.showMessage(
            f'   {dir_count} 个文件夹  ·  {file_count} 个文件')

    # ── 右键菜单 ────────────────────────────────────────────────────────

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 7px 36px 7px 16px;
                border-radius: 4px;
                font-size: 13px;
                color: {Colors.TEXT};
            }}
            QMenu::item:selected {{
                background: {Colors.ACCENT_BG};
            }}
        """)
        mode = reload_config().get('download', 'mode', fallback='aria2') if reload_config().has_section('download') else 'aria2'
        dl_label = '  内建下载' if mode == 'builtin' else '  下载到 aria2'
        act_dl = menu.addAction(dl_label)
        menu.addSeparator()
        act_del = menu.addAction('  删除')
        act_rename = menu.addAction('  重命名')
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == act_dl:
            self._download_selected()
        elif action == act_del:
            self._delete_selected()
        elif action == act_rename:
            self._rename_selected()

    # ── 文件操作 ────────────────────────────────────────────────────────

    def _get_selected_items(self):
        """返回 [(path, is_dir, fs_id), ...]"""
        items = []
        seen = set()
        for idx in self.table.selectedIndexes():
            if idx.column() != 0:
                continue
            item = self.table.item(idx.row(), 0)
            if item:
                data = item.data(Qt.UserRole)
                if data and data['fs_id'] not in seen:
                    seen.add(data['fs_id'])
                    items.append((data['path'], data.get('isdir') == 1, data['fs_id']))
        return items

    def _get_selected_paths(self):
        return [p for p, _, _ in self._get_selected_items()]

    def _download_selected(self):
        items = self._get_selected_items()
        if not items:
            # 没选中，下载当前目录
            items = [(self.account.current_dir, True, None)]

        mode = reload_config().get('download', 'mode', fallback='aria2') if reload_config().has_section('download') else 'aria2'
        target = '内建下载器' if mode == 'builtin' else 'aria2'
        names = '\n'.join(p for p, _, _ in items)
        reply = QMessageBox.question(self, '确认下载',
            f'确定下载以下内容到 {target}？\n\n{names}\n\n共 {len(items)} 项',
            QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        dlg = getattr(self, '_dl_manager', None)
        if dlg is None or not dlg.isVisible():
            dlg = DownloadManager(self)
        dlg.all_done.connect(self._on_all_downloads_done)
        self._dl_manager = dlg

        task_infos = {}
        for path, is_dir, fsid in items:
            info = dlg.add_task(path)
            task_infos[path] = info

        dlg.show()
        dlg.raise_()

        for path, is_dir, fsid in items:
            self._start_download_task(path, task_infos[path], is_dir, fsid)

    def _show_download_manager(self):
        """重新打开下载管理器（如果存在的话）"""
        dlg = getattr(self, '_dl_manager', None)
        if dlg is None:
            QMessageBox.information(self, '提示', '暂无下载任务')
            return
        dlg.show()
        dlg.raise_()

    def _start_download_task(self, path, task_info, is_dir=True, fs_id=None):
        worker = UpdatedDownloadWorker(self.account, path, is_dir, fs_id)
        if not hasattr(self, '_dl_workers'):
            self._dl_workers = []
        self._dl_workers.append(worker)

        task_info['status'].setText('获取链接中...')

        worker.dl_progress.connect(lambda f, d, t, ti=task_info:
            self._dl_manager.update_task(ti, '下载中',
                int(d * 100 / t) if t > 0 else 0,
                f'{sizeof_fmt(d)} / {sizeof_fmt(t)}' if t > 0 else sizeof_fmt(d)))
        worker.dl_file_done.connect(lambda f, ti=task_info:
            self._dl_manager.update_task(ti, '下载中', None,
                f'{PurePosixPath(f).name} 完成'))
        worker.download_finished.connect(lambda success, msg, count, w=worker, ti=task_info:
            self._on_task_finished(ti, success, msg, w))

        worker.start()
        # 状态栏显示活动下载数
        active = len([w for w in self._dl_workers if w.isRunning()])
        self.status_bar.showMessage(f'  下载任务进行中 ({active} 个)...')

    def _on_task_finished(self, task_info, success, message, worker):
        # 等待线程彻底结束再移除引用，防止 QThread destroyed 错误
        worker.wait(3000)
        if hasattr(self, '_dl_workers') and worker in self._dl_workers:
            self._dl_workers.remove(worker)
        if success:
            task_info['bar'].setValue(100)
            self._dl_manager.update_task(task_info, '完成', 100, message)
        else:
            self._dl_manager.update_task(task_info, '失败', 0, message)

    def _on_builtin_dl_ready(self, task_info, dl):
        dl.progress.connect(lambda fname, done, total, ti=task_info:
            self._dl_manager.update_task(ti, '下载中',
                int(done * 100 / total) if total > 0 else 0,
                f'{sizeof_fmt(done)} / {sizeof_fmt(total)}' if total > 0 else sizeof_fmt(done)))
        dl.file_done.connect(lambda fname, ti=task_info:
            self._dl_manager.update_task(ti, '下载中', None,
                f'{PurePosixPath(fname).name} 完成'))

    def _on_all_downloads_done(self):
        self.status_bar.showMessage('  所有下载任务已完成', 5000)
        # 清理已完成的 worker
        if hasattr(self, '_dl_workers'):
            self._dl_workers = [w for w in self._dl_workers if w.isRunning()]

    def _delete_selected(self):
        paths = self._get_selected_paths()
        if not paths:
            return QMessageBox.information(self, '提示', '请先选中要删除的文件或文件夹')
        names = '\n'.join(paths)
        reply = QMessageBox.warning(
            self, '确认删除',
            f'确定要删除以下内容？\n\n{names}\n\n此操作不可撤销！',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.worker_del = DeleteWorker(self.account, paths)
        self.worker_del.finished.connect(self._on_delete_finished)
        self._safe_start(self.worker_del)
        self.status_bar.showMessage('正在删除...')

    def _on_delete_finished(self, success, message):
        if success:
            self.status_bar.showMessage('  删除成功', 3000)
            self._refresh_file_list()
        else:
            QMessageBox.critical(self, '删除失败', message)

    def _rename_selected(self):
        paths = self._get_selected_paths()
        if len(paths) != 1:
            return QMessageBox.information(self, '提示', '请只选中一个文件进行重命名')
        old_path = paths[0]
        old_name = PurePosixPath(old_path).name
        new_name, ok = QInputDialog.getText(self, '重命名', '新名称：', text=old_name)
        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return
        self.worker_rename = RenameWorker(self.account, old_path, new_name.strip())
        self.worker_rename.finished.connect(self._on_rename_finished)
        self._safe_start(self.worker_rename)
        self.status_bar.showMessage('正在重命名...')

    def _on_rename_finished(self, success, message):
        if success:
            self.status_bar.showMessage(f'  {message}', 3000)
            self._refresh_file_list()
        else:
            QMessageBox.critical(self, '重命名失败', message)

    def _find_file_by_path(self, path):
        for f in self._current_files:
            if f.get('path') == path:
                return f
        return None

    # ── 账户操作 ────────────────────────────────────────────────────────

    def _refresh_token(self):
        self.worker_token = RefreshTokenWorker(self.account)
        self.worker_token.finished.connect(self._on_token_refreshed)
        self._safe_start(self.worker_token)
        self.status_bar.showMessage('正在刷新 Token...')

    def _on_token_refreshed(self, success, message):
        if success:
            QMessageBox.information(self, '成功', message)
        else:
            QMessageBox.critical(self, '失败', message)

    def _switch_account(self):
        reply = QMessageBox.question(self, '切换账户', '返回登录界面，确定？', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.account = None
            self.close()

    def _logout(self):
        reply = QMessageBox.warning(self, '注销账户', '将删除本地存储的账户信息。确定？',
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.account.logout()
            self.account = None
            self.close()

    def _show_error(self, title, text):
        QMessageBox.critical(self, title, text)

    def _open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def _show_about(self):
        QMessageBox.about(self, '关于 baidu-linux',
                          '<h3 style="color:#1e293b;">baidu-linux</h3>'
                          '<p style="color:#64748b;">百度网盘桌面客户端</p>'
                          '<p style="color:#94a3b8;font-size:11px;">'
                          'Powered by PySide6 · 百度网盘开放 API</p>')


# ═══════════════════════════════════════════════════════════════════════════
# 应用入口
# ═══════════════════════════════════════════════════════════════════════════

class Application:

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName('baidu-linux')
        self._window = None

    def run(self):
        while True:
            account = self._show_login()
            if account is None:
                break
            self._window = MainWindow(account)
            self._window.show()
            self.app.exec()
            if self._window.account is not None:
                break
        return 0

    def _show_login(self):
        dlg = LoginDialog()
        if dlg.exec() == QDialog.Accepted:
            return dlg.account_obj
        return None


def main():
    app = Application()
    sys.exit(app.run())


if __name__ == '__main__':
    main()

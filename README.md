# baidu-linux

百度网盘 Linux/Windows 客户端 — CLI + GUI (PySide6)

Original API Document <https://pan.baidu.com/union/document>

## 安装

```bash
pip install -r requirements.txt
```

## 使用方式

### GUI 模式 (推荐)

```bash
python gui.py
```

GUI 功能：
- 账户管理（添加 / 切换 / 注销）
- 网盘文件浏览（双击进入文件夹、工具栏导航）
- 文件操作（下载到 aria2、删除、重命名）
- 右键上下文菜单
- Token 自动 / 手动刷新

### CLI 模式

```bash
python baidu.py
```

## config.ini 配置

```ini
[api_config]
client_id = 你的 app_id
client_secret = 你的 app_secret

[aria2]
rpc = www.example.com
secret = secret
port = 6800
schema = http

# 账户信息由程序自动添加
[name1]
access_token =
refresh_token =
scope =
```

## client_id 和 client_secret

需要在百度开发者平台申请：<http://developer.baidu.com/console#app/project>

> **注意**：需要通过实名认证

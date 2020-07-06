# baidu-linux
Original API Document https://pan.baidu.com/union/document

## client_id and client_secret
client_id and client_secret you need to apply it at
http://developer.baidu.com/console#app/project

### Attention! You need to verify your account with your real personal information

config.ini example
```
[api_config]
client_id =
client_secret =

[aria2]
rpc = www.example.com
secret = secret
port = 6800
schema = http

# it will be added automaticly after add a account
[name1]
access_token =
refresh_token =
scope =
```

## Downloadlink
Please don't add to many download tasks, because the download link only valid for 8 hours. Download links can be added at most 1000 one time.

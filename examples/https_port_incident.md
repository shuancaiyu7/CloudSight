# HTTPS 网站连接超时：示例故障资料

## 用户反馈

- 用户访问 `https://demo.example.com` 时，浏览器长时间等待后提示连接超时。
- 该问题出现在一次 Nginx 配置发布之后。
- 这是一份演示资料，不对应真实服务器或真实域名。

## 已知现象

- 外部安全规则已允许 TCP 443 入站。
- 服务器上的 443 端口未处于监听状态。
- 应用服务仍在运行，但 Nginx 服务启动失败。

## 日志片段

```text
nginx[1820]: bind() to 0.0.0.0:443 failed (98: Address already in use)
systemd[1]: nginx.service: Failed with result 'exit-code'
```

## 配置摘要

- `/etc/nginx/conf.d/site.conf` 在最近一次发布时被修改。
- 当前需要先确认端口占用情况和 Nginx 配置语法。
- 未经人工确认，不应直接重启生产服务或删除配置文件。

## 期望排查方向

1. 检查 Nginx 服务状态及错误日志。
2. 确认 443 端口被哪个服务占用，或是否缺少监听配置。
3. 对 Nginx 配置进行语法检查，确认后再由人工执行变更。

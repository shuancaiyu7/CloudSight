# DNS 解析失败排查手册

先区分域名拼写错误、DNS 服务器不可达和缓存过期。检查 resolv.conf、DNS 地址的 UDP/TCP 53 端口连通性，并使用 nslookup 或 dig 对比多个解析服务器。涉及生产配置变更时应由人工复核。

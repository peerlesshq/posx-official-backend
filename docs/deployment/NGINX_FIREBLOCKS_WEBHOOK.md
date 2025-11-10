# 🔒 Nginx Fireblocks Webhook 配置

**v2.2.1 安全加固**

---

## 📋 配置目的

在 MOCK 环境中，为 Fireblocks webhook 端点添加 **Nginx层 IP 限制**，与代码层防护形成**双重防御**。

---

## 🎯 防护层次

| 层次 | 位置 | 防护措施 |
|------|------|----------|
| **Layer 1** | Nginx/WAF | IP 白名单 (MOCK环境) |
| **Layer 2** | Django代码 | `_is_local_ip()` 检查 |
| **Layer 3** | Django代码 | `X-MOCK-WEBHOOK` 头检测 |

---

## 🔧 MOCK 环境配置

### Nginx 配置示例

**文件**: `/etc/nginx/sites-available/posx-backend-mock`

```nginx
# ========================================
# POSX Backend - MOCK 环境
# ========================================

upstream backend_mock {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name mock-api.posx.local;  # MOCK 环境域名
    
    # 通用API路由
    location / {
        proxy_pass http://backend_mock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # ⭐ Fireblocks Webhook 特殊限制（MOCK环境）
    location /api/v1/webhooks/fireblocks/ {
        # 仅允许本地IP访问
        allow 127.0.0.1;
        allow ::1;
        
        # 如需允许特定开发机器，添加其IP
        # allow 192.168.1.100;  # 示例：开发者机器
        
        deny all;  # ⭐ 拒绝所有其他IP
        
        # 代理到后端
        proxy_pass http://backend_mock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }
    
    # 日志
    access_log /var/log/nginx/posx-mock-access.log combined;
    error_log /var/log/nginx/posx-mock-error.log warn;
}
```

---

## 🔥 LIVE 环境配置

### Nginx 配置示例

**文件**: `/etc/nginx/sites-available/posx-backend-prod`

```nginx
# ========================================
# POSX Backend - LIVE 生产环境
# ========================================

upstream backend_prod {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl http2;
    server_name api.posx.io;  # 生产域名
    
    # SSL证书配置
    ssl_certificate /etc/letsencrypt/live/api.posx.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.posx.io/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # 通用API路由
    location / {
        proxy_pass http://backend_prod;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # ⭐ Fireblocks Webhook（生产环境 - IP白名单）
    location /api/v1/webhooks/fireblocks/ {
        # ⭐ Fireblocks 官方出口 IP 段（需定期更新）
        # 从 Fireblocks 文档获取最新 IP: https://developers.fireblocks.com/docs
        allow 34.225.112.0/24;
        allow 52.5.67.0/24;
        allow 52.222.0.0/16;      # 示例 - 实际需确认
        allow 18.208.0.0/13;      # 示例 - 实际需确认
        
        deny all;  # ⭐ 拒绝所有其他IP
        
        # 代理到后端
        proxy_pass http://backend_prod;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置（生产环境更宽容）
        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # 限流（可选）
        limit_req zone=webhook_limit burst=10 nodelay;
    }
    
    # 日志
    access_log /var/log/nginx/posx-prod-access.log combined;
    error_log /var/log/nginx/posx-prod-error.log warn;
}

# ========================================
# 限流配置（在 http 块中）
# ========================================
# http {
#     limit_req_zone $binary_remote_addr zone=webhook_limit:10m rate=10r/s;
# }
```

---

## ⚙️ 部署步骤

### 1. 创建配置文件

```bash
# MOCK 环境
sudo nano /etc/nginx/sites-available/posx-backend-mock

# LIVE 环境
sudo nano /etc/nginx/sites-available/posx-backend-prod
```

### 2. 启用站点

```bash
# MOCK
sudo ln -s /etc/nginx/sites-available/posx-backend-mock /etc/nginx/sites-enabled/

# LIVE
sudo ln -s /etc/nginx/sites-available/posx-backend-prod /etc/nginx/sites-enabled/
```

### 3. 测试配置

```bash
sudo nginx -t
```

**预期输出**:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 4. 重载 Nginx

```bash
sudo systemctl reload nginx
```

---

## ✅ 验证测试

### MOCK 环境测试

```bash
# 1. 从本地访问（应成功）
curl -X POST http://localhost/api/v1/webhooks/fireblocks/ \
  -H "Content-Type: application/json" \
  -H "X-MOCK-WEBHOOK: true" \
  -d '{"type":"test","txId":"test-123"}'

# 预期：200 OK 或 400 (签名错误)

# 2. 从外部IP访问（应被拒绝）
curl -X POST http://mock-api.posx.local/api/v1/webhooks/fireblocks/ \
  -H "Content-Type: application/json" \
  -d '{"type":"test"}'

# 预期：403 Forbidden
```

### LIVE 环境测试

```bash
# 1. 从 Fireblocks IP 访问（应成功）
# 需要从 Fireblocks 服务器测试

# 2. 从其他IP访问（应被拒绝）
curl -X POST https://api.posx.io/api/v1/webhooks/fireblocks/ \
  -H "Content-Type: application/json" \
  -d '{"type":"test"}'

# 预期：403 Forbidden
```

---

## 🔄 IP 白名单更新

### Fireblocks IP 段获取

1. 访问 [Fireblocks 开发者文档](https://developers.fireblocks.com/docs/webhook-notifications)
2. 查找 "Webhook Source IPs" 或 "IP Whitelist"
3. 复制官方提供的 IP 段

### 更新流程

```bash
# 1. 编辑配置
sudo nano /etc/nginx/sites-available/posx-backend-prod

# 2. 添加新 IP 段
# allow NEW_IP_RANGE;

# 3. 测试配置
sudo nginx -t

# 4. 重载
sudo systemctl reload nginx

# 5. 验证
curl -v https://api.posx.io/api/v1/webhooks/fireblocks/
```

---

## 🚨 故障排查

### 问题 1: 403 Forbidden（本地测试）

**原因**: Nginx IP 白名单配置过严

**解决**:
```bash
# 检查 Nginx 错误日志
sudo tail -f /var/log/nginx/posx-mock-error.log

# 确认配置中有 allow 127.0.0.1;
```

### 问题 2: Fireblocks Webhook 未收到

**原因**: IP 白名单中缺少 Fireblocks 新 IP

**解决**:
1. 检查 Nginx 日志查看被拒绝的 IP
2. 确认该 IP 是否为 Fireblocks 官方 IP
3. 添加到白名单并重载

### 问题 3: 502 Bad Gateway

**原因**: 后端服务未运行

**解决**:
```bash
# 检查 Django 服务
sudo systemctl status posx-backend

# 检查端口
sudo netstat -tlnp | grep 8000
```

---

## 📊 监控建议

### Nginx 日志监控

```bash
# 实时监控访问日志
tail -f /var/log/nginx/posx-prod-access.log | grep "/webhooks/fireblocks/"

# 统计 403 错误
grep "webhooks/fireblocks" /var/log/nginx/posx-prod-access.log | grep " 403 " | wc -l
```

### Grafana 仪表板

监控指标：
- `nginx_http_requests_total{location="/api/v1/webhooks/fireblocks/", status="403"}`
- `nginx_http_requests_total{location="/api/v1/webhooks/fireblocks/", status="200"}`

---

## 🔐 安全最佳实践

1. ✅ **分层防御**: Nginx + Django 双重验证
2. ✅ **最小权限**: 仅允许必要的 IP
3. ✅ **定期更新**: 每季度检查 Fireblocks IP 段
4. ✅ **日志审计**: 保留至少 90 天日志
5. ✅ **监控告警**: 异常 403 错误触发告警

---

## 📚 相关文档

- **Webhook 配置**: `docs/config/CONFIG_WEBHOOKS.md`
- **Phase E 交付**: `docs/phases/PHASE_E_IMPLEMENTATION_COMPLETE.md`
- **Fireblocks 官方文档**: https://developers.fireblocks.com/docs

---

**最后更新**: 2025-11-09  
**维护者**: DevOps Team


# ⚙️ Phase E 环境变量配置指南

**Phase**: E - Vesting 代币分期释放  
**更新时间**: 2025-11-09

---

## 📋 必需配置项

### 1. Fireblocks 运行模式

```bash
# 运行模式（MOCK=开发测试，LIVE=生产）
FIREBLOCKS_MODE=MOCK

# LIVE模式双保险开关（仅生产环境设为 1）
ALLOW_PROD_TX=0
```

**说明：**
- `FIREBLOCKS_MODE=MOCK`：使用模拟客户端，无需真实凭证
- `FIREBLOCKS_MODE=LIVE`：使用真实 Fireblocks API
- `ALLOW_PROD_TX`：LIVE 模式的额外保护开关

---

### 2. MOCK 模式配置

```bash
# 模拟交易完成延迟（秒）
MOCK_TX_COMPLETE_DELAY=3

# MOCK Webhook 回调地址
MOCK_WEBHOOK_URL=http://localhost:8000/api/v1/webhooks/fireblocks/
```

**说明：**
- `MOCK_TX_COMPLETE_DELAY`：模拟链上确认的延迟时间
- `MOCK_WEBHOOK_URL`：MOCK 客户端发送 webhook 的目标地址

---

### 3. LIVE 模式配置（⚠️ 仅生产环境）

```bash
# Fireblocks API 凭证（⚠️ 开发环境留空）
FIREBLOCKS_API_KEY=
FIREBLOCKS_PRIVATE_KEY=
FIREBLOCKS_BASE_URL=https://api.fireblocks.io
FIREBLOCKS_VAULT_ACCOUNT_ID=0
FIREBLOCKS_ASSET_ID=POSX_ETH
```

**获取方式：**
1. 登录 [Fireblocks Console](https://console.fireblocks.io/)
2. 进入 **Settings → API Users**
3. 创建 API User（权限：Transaction Signing）
4. 下载私钥（PEM 格式）
5. 将完整的 PEM 内容（包含 `-----BEGIN PRIVATE KEY-----` 和 `-----END PRIVATE KEY-----`）配置到 `FIREBLOCKS_PRIVATE_KEY`

**⚠️ 注意：**
- 私钥格式必须保留换行符（多行配置）
- 或使用 Base64 编码后配置（单行）

---

### 4. Webhook 签名验证（⚠️ 仅生产环境）

```bash
# Webhook 公钥（支持双公钥轮换）
FIREBLOCKS_WEBHOOK_PUBLIC_KEY=
FIREBLOCKS_WEBHOOK_PUBLIC_KEY_2=
```

**获取方式：**
1. 在 Fireblocks Console 中创建 Webhook
2. 复制提供的公钥（PEM 格式）
3. 配置到环境变量

**双公钥轮换：**
- `FIREBLOCKS_WEBHOOK_PUBLIC_KEY`：主公钥
- `FIREBLOCKS_WEBHOOK_PUBLIC_KEY_2`：备用公钥（公钥轮换期间使用）

---

## 🎯 完整配置示例

### 开发/测试环境

```bash
# ========================================
# Phase E: Vesting 配置（开发环境）
# ========================================

# 运行模式
FIREBLOCKS_MODE=MOCK
ALLOW_PROD_TX=0

# MOCK 配置
MOCK_TX_COMPLETE_DELAY=3
MOCK_WEBHOOK_URL=http://localhost:8000/api/v1/webhooks/fireblocks/

# LIVE 配置（留空）
FIREBLOCKS_API_KEY=
FIREBLOCKS_PRIVATE_KEY=
FIREBLOCKS_BASE_URL=https://api.fireblocks.io
FIREBLOCKS_VAULT_ACCOUNT_ID=0
FIREBLOCKS_ASSET_ID=POSX_ETH
FIREBLOCKS_WEBHOOK_PUBLIC_KEY=
FIREBLOCKS_WEBHOOK_PUBLIC_KEY_2=
```

### 生产环境

```bash
# ========================================
# Phase E: Vesting 配置（生产环境）
# ========================================

# 运行模式 ⚠️
FIREBLOCKS_MODE=LIVE
ALLOW_PROD_TX=1

# MOCK 配置（生产环境不使用）
MOCK_TX_COMPLETE_DELAY=3
MOCK_WEBHOOK_URL=

# LIVE 配置 ⚠️
FIREBLOCKS_API_KEY=<your-api-key>
FIREBLOCKS_PRIVATE_KEY=<your-private-key-pem>
FIREBLOCKS_BASE_URL=https://api.fireblocks.io
FIREBLOCKS_VAULT_ACCOUNT_ID=<your-vault-id>
FIREBLOCKS_ASSET_ID=POSX_ETH
FIREBLOCKS_WEBHOOK_PUBLIC_KEY=<webhook-public-key-pem>
FIREBLOCKS_WEBHOOK_PUBLIC_KEY_2=
```

---

## ✅ 配置检查清单

### 开发环境
- [ ] `FIREBLOCKS_MODE=MOCK`
- [ ] `ALLOW_PROD_TX=0`
- [ ] `MOCK_WEBHOOK_URL` 配置为本地地址
- [ ] Fireblocks API 配置留空

### 生产环境
- [ ] `FIREBLOCKS_MODE=LIVE`
- [ ] `ALLOW_PROD_TX=1`（仔细确认！）
- [ ] `FIREBLOCKS_API_KEY` 已配置
- [ ] `FIREBLOCKS_PRIVATE_KEY` 已配置（完整 PEM）
- [ ] `FIREBLOCKS_VAULT_ACCOUNT_ID` 已配置
- [ ] `FIREBLOCKS_ASSET_ID` 正确（如 POSX_ETH）
- [ ] `FIREBLOCKS_WEBHOOK_PUBLIC_KEY` 已配置

---

## 🔐 安全注意事项

### 1. 私钥保护
- ❌ **绝不** 提交到 Git
- ❌ **绝不** 明文存储在代码中
- ✅ 使用环境变量或密钥管理服务
- ✅ 生产环境使用加密存储（如 AWS Secrets Manager）

### 2. 双保险机制
- LIVE 模式需要同时满足：
  1. `FIREBLOCKS_MODE=LIVE`
  2. `ALLOW_PROD_TX=1`
- 防止误操作触发生产交易

### 3. Webhook 安全
- MOCK 模式：仅允许本地 IP 访问
- LIVE 模式：
  - IP 白名单验证
  - RSA-SHA512 签名验证
  - 支持双公钥轮换

---

## 📚 相关文档

- **Webhook 配置**: `docs/config/CONFIG_WEBHOOKS.md`
- **环境变量总览**: `docs/config/CONFIG_ENV_SETUP.md`
- **Phase E 交付**: `docs/phases/PHASE_E_DELIVERY.md`

---

## 🆘 常见问题

### Q1: MOCK 模式下收不到 webhook？

**A:** 检查以下几点：
1. Django 服务器运行在 8000 端口
2. Celery worker 正在运行
3. `MOCK_WEBHOOK_URL` 配置正确
4. 查看 Celery 日志：`[MOCK Webhook] Sent successfully`

### Q2: LIVE 模式下如何测试？

**A:** 
1. 先在 Fireblocks Console 的 Sandbox 环境测试
2. 设置 `FIREBLOCKS_BASE_URL=https://sandbox-api.fireblocks.io`
3. 使用测试资产（如 ETH_TEST）
4. 确认无误后再切换到生产环境

### Q3: 私钥配置格式错误？

**A:** 
- 方式1：直接配置（保留换行）
  ```bash
  FIREBLOCKS_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
  MIIEvgIBADANBgkqhkiG9w0...
  ...
  -----END PRIVATE KEY-----"
  ```

- 方式2：Base64 编码后配置（单行）
  ```bash
  FIREBLOCKS_PRIVATE_KEY=<base64-encoded-pem>
  ```

---

**最后更新**: 2025-11-09  
**维护者**: POSX Team


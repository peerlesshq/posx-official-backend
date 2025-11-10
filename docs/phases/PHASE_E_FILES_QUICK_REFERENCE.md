# 📚 Phase E 文件快速参考

**快速查找所有创建/修改的文件**

---

## ✅ 新建文件（17个）

### 数据模型
```
backend/apps/vesting/models.py                              # Vesting 三表模型（200行）
backend/apps/vesting/__init__.py                            # App 初始化
backend/apps/vesting/apps.py                                # App 配置
backend/apps/vesting/migrations/__init__.py                 # 迁移目录
```

### 工具函数
```
backend/apps/allocations/utils/__init__.py                  # Utils 包
backend/apps/allocations/utils/address.py                   # 多链地址校验（105行）
backend/apps/vesting/ports.py                               # 接口定义（38行）
```

### 客户端层
```
backend/apps/vesting/services/__init__.py                   # Services 包
backend/apps/vesting/services/mock_fireblocks_client.py     # MOCK 客户端（87行）
backend/apps/vesting/services/fireblocks_client.py          # LIVE 客户端（235行）
backend/apps/vesting/services/client_factory.py             # 客户端工厂（26行）
```

### 业务逻辑
```
backend/apps/vesting/services/batch_release_service.py      # 批量发放服务（252行）
backend/apps/webhooks/views/__init__.py                     # Views 包
backend/apps/webhooks/views/fireblocks_webhook.py           # Webhook 处理器（242行）
backend/apps/webhooks/utils/fireblocks_crypto.py            # RSA 签名验证（47行）
```

### 管理界面 + 任务
```
backend/apps/vesting/admin.py                               # Django Admin（275行）
backend/apps/vesting/tasks.py                               # Celery 任务（280行）
```

### 文档
```
docs/config/CONFIG_PHASE_E_ENV.md                           # 环境变量指南（250行）
docs/phases/PHASE_E_IMPLEMENTATION_COMPLETE.md              # 实施完成报告
docs/phases/PHASE_E_FILES_QUICK_REFERENCE.md                # 本文档
```

---

## ✏️ 修改文件（4个）

### 数据模型
```
backend/apps/sites/models.py                                # + ChainAssetConfig 模型（+58行）
backend/apps/webhooks/models.py                             # ~ IdempotencyKey 唯一约束（~10行）
backend/apps/allocations/models.py                          # + released_tokens 字段（+15行）
```

### 配置文件
```
backend/apps/webhooks/utils/idempotency.py                  # ~ 使用 IntegrityError（~15行）
backend/apps/webhooks/urls.py                               # + Fireblocks 路由（+4行）
backend/config/settings/base.py                             # + Fireblocks 配置 + Celery Beat（+35行）
```

---

## 📂 目录结构

```
backend/apps/
├── vesting/                           # ⭐ 新建 App
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                      # VestingPolicy/Schedule/Release
│   ├── admin.py                       # Admin 管理界面
│   ├── tasks.py                       # Celery 定时任务
│   ├── ports.py                       # 接口定义
│   ├── migrations/
│   │   └── __init__.py
│   └── services/
│       ├── __init__.py
│       ├── mock_fireblocks_client.py  # MOCK 客户端
│       ├── fireblocks_client.py       # LIVE 客户端
│       ├── client_factory.py          # 工厂类
│       └── batch_release_service.py   # 批量发放
│
├── allocations/
│   ├── models.py                      # ✏️ + released_tokens
│   └── utils/
│       ├── __init__.py                # ⭐ 新建
│       └── address.py                 # ⭐ 地址校验
│
├── webhooks/
│   ├── models.py                      # ✏️ IdempotencyKey
│   ├── urls.py                        # ✏️ + Fireblocks 路由
│   ├── views/
│   │   ├── __init__.py                # ⭐ 新建
│   │   └── fireblocks_webhook.py      # ⭐ Webhook 处理器
│   └── utils/
│       ├── idempotency.py             # ✏️ IntegrityError
│       └── fireblocks_crypto.py       # ⭐ RSA 验证
│
└── sites/
    └── models.py                      # ✏️ + ChainAssetConfig

config/settings/
└── base.py                            # ✏️ + Fireblocks + Celery Beat

docs/
├── config/
│   ├── CONFIG_PHASE_E_ENV.md          # ⭐ 环境变量指南
│   └── CONFIG_WEBHOOKS.md             # (已存在)
└── phases/
    ├── PHASE_E_IMPLEMENTATION_COMPLETE.md  # ⭐ 实施报告
    └── PHASE_E_FILES_QUICK_REFERENCE.md    # ⭐ 本文档
```

---

## 🔑 关键文件说明

### 必读文件（开始前）

1. **`docs/phases/PHASE_E_IMPLEMENTATION_COMPLETE.md`**  
   完整的实施报告，包含功能说明、下一步操作、验收清单

2. **`docs/config/CONFIG_PHASE_E_ENV.md`**  
   环境变量配置指南，包含 MOCK/LIVE 模式配置

3. **`backend/apps/vesting/models.py`**  
   数据模型定义，了解 Vesting 核心结构

### 核心业务逻辑

1. **`backend/apps/vesting/services/batch_release_service.py`**  
   批量发放核心逻辑，包含站点隔离、状态更新、累加 allocation

2. **`backend/apps/webhooks/views/fireblocks_webhook.py`**  
   Webhook 处理器，包含 MOCK/LIVE 安全验证、幂等性保障

3. **`backend/apps/vesting/admin.py`**  
   Admin 管理界面，包含批量发放 Action、状态着色

### 客户端实现

1. **`backend/apps/vesting/services/mock_fireblocks_client.py`**  
   MOCK 客户端，开发测试使用

2. **`backend/apps/vesting/services/fireblocks_client.py`**  
   LIVE 客户端，生产环境使用

3. **`backend/apps/vesting/services/client_factory.py`**  
   工厂类，自动选择实现

### 定时任务

1. **`backend/apps/vesting/tasks.py`**  
   - `unlock_vesting_releases` - 每天解锁
   - `reconcile_stuck_releases` - 每5分钟对账
   - `cleanup_old_idempotency_keys` - 每天清理

---

## 📊 代码量统计

| 类型 | 数量 | 总行数 |
|------|------|--------|
| 新建文件 | 17 | ~2300 |
| 修改文件 | 4 | ~130 |
| **总计** | **21** | **~2430** |

---

## 🚀 快速开始

### 1. 查看实施报告
```bash
cat docs/phases/PHASE_E_IMPLEMENTATION_COMPLETE.md
```

### 2. 配置环境变量
```bash
# 参考配置指南
cat docs/config/CONFIG_PHASE_E_ENV.md

# 添加到 .env
echo "FIREBLOCKS_MODE=MOCK" >> .env
echo "ALLOW_PROD_TX=0" >> .env
```

### 3. 运行迁移
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### 4. 启动服务
```bash
# 终端 1
python manage.py runserver

# 终端 2
celery -A config worker -l info

# 终端 3
celery -A config beat -l info
```

### 5. 访问 Admin
```
http://localhost:8000/admin/vesting/vestingrelease/
```

---

**Phase E 实施完成！** 🎉

所有文件已就位，准备测试！


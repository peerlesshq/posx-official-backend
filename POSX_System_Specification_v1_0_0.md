# POSX 系统规范文档 v1.0

**文档类型：** 系统架构与业务规范  
**文档版本：** v1.0.0  
**发布日期：** 2025-11-07  
**文档状态：** 正式发布 ✅  
**适用范围：** 全系统（Backend + Frontend + Infrastructure）

---

## 📋 目录

1. [文档概述](#1-文档概述)
2. [系统概述](#2-系统概述)
3. [核心业务规则](#3-核心业务规则)
4. [技术架构规则](#4-技术架构规则)
5. [数据模型规范](#5-数据模型规范)
6. [API 设计规范](#6-api-设计规范)
7. [认证与授权规范](#7-认证与授权规范)
8. [支付与订单规范](#8-支付与订单规范)
9. [代币分配规范](#9-代币分配规范)
10. [佣金系统规范](#10-佣金系统规范)
11. [安全规范](#11-安全规范)
12. [环境配置规范](#12-环境配置规范)
13. [部署规范](#13-部署规范)
14. [运维规范](#14-运维规范)
15. [监控与告警规范](#15-监控与告警规范)
16. [术语表](#16-术语表)

---

## 1. 文档概述

### 1.1 文档目的

本文档定义 POSX 代币预售平台的完整系统规范，包括业务规则、技术架构、数据模型、API 设计、安全策略和运维规范。

### 1.2 目标读者

- 开发工程师（Backend/Frontend）
- 系统架构师
- DevOps 工程师
- 产品经理
- AI 辅助开发系统

### 1.3 文档约定

```yaml
规范级别:
  MUST: 必须遵守（强制性）
  SHOULD: 应该遵守（推荐）
  MAY: 可以选择（可选）
  MUST_NOT: 禁止（严格禁止）

变更管理:
  - 重大变更需要架构评审
  - 所有变更需要版本号递增
  - 破坏性变更需要迁移计划
```

### 1.4 版本历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0.0 | 2025-11-07 | 初始正式版本 | System Architect |

---

## 2. 系统概述

### 2.1 系统简介

POSX 是一个多站点、多币种的代币预售平台，支持：
- 用户注册与 KYC
- 多档位代币购买
- 多层级推荐佣金
- 代币锁仓与释放
- 多站点独立运营

### 2.2 系统边界

```yaml
系统范围:
  - Web 应用（用户端）
  - Admin 后台（管理端）
  - RESTful API（后端服务）
  - Webhook 处理（第三方集成）
  - 定时任务（后台任务）

外部依赖:
  - Auth0: 用户认证
  - Stripe: 支付处理
  - Fireblocks: 代币托管与分发
  - WalletConnect: Web3 钱包连接
  - PostgreSQL: 主数据库
  - Redis: 缓存与队列
  - Celery: 异步任务
```

### 2.3 核心能力

```yaml
用户能力:
  - 多种方式注册登录（Email/Passkey/Wallet）
  - 浏览档位信息
  - 购买代币（Stripe 支付）
  - 查看订单历史
  - 查看代币余额（总量/锁仓/可用）
  - 推荐新用户获得佣金

管理员能力:
  - 站点管理
  - 档位配置
  - 订单管理
  - 手动发放代币（通过 Fireblocks）
  - 佣金配置与结算
  - 用户管理
  - 数据分析

系统能力:
  - 高并发订单处理
  - 幂等性保证
  - 库存精确控制
  - 多层级佣金计算
  - 定时任务执行
  - 监控与告警
```

---

## 3. 核心业务规则

### 3.1 业务原则

```yaml
原则 1: 无退款政策
  规则:
    - MUST_NOT 支持订单退款
    - MUST_NOT 支持订单取消（支付后）
    - MUST 监控银行拒付（dispute）
    - MUST 记录争议信息（不改订单状态）
  
  理由:
    - 代币预售特性
    - 简化财务流程
    - 银行拒付仍需监控

原则 2: 手动发币
  规则:
    - MUST_NOT 自动发放代币
    - MUST 由管理员手动操作
    - MUST 通过 Fireblocks API
    - MUST 记录所有发放状态
  
  理由:
    - 合规要求
    - 风控需要
    - 可审计性

原则 3: 钱包地址必填
  规则:
    - MUST 在支付前填写钱包地址
    - MUST 验证钱包地址格式
    - MUST 统一使用小写存储
    - MUST_NOT 允许重复绑定
  
  理由:
    - 代币接收必需
    - 避免发放错误

原则 4: 数据一致性
  规则:
    - MUST 使用数据库事务
    - MUST 实现幂等性
    - MUST 使用乐观锁控制库存
    - MUST 记录所有状态变更
  
  理由:
    - 避免超卖
    - 保证数据准确

原则 5: 多站点隔离
  规则:
    - MUST 按站点隔离数据
    - MUST 独立的档位配置
    - MUST 独立的佣金配置
    - SHOULD 共享用户体系
  
  理由:
    - 不同地区运营
    - 合规要求
```

### 3.2 订单生命周期

```yaml
订单状态定义:
  pending:
    描述: 待支付
    可转换至: [paid, failed, cancelled]
    超时: 15 分钟
  
  paid:
    描述: 已支付
    可转换至: []
    终态: true
  
  failed:
    描述: 支付失败
    可转换至: []
    终态: true
  
  cancelled:
    描述: 已取消（超时）
    可转换至: []
    终态: true

状态转换规则:
  pending → paid:
    触发: Stripe payment_intent.succeeded
    动作:
      - 更新订单状态
      - 记录 paid_at
      - 生成多层级佣金
      - 创建分配记录（status=pending）
  
  pending → failed:
    触发: Stripe payment_intent.payment_failed
    动作:
      - 更新订单状态
      - 记录失败原因
      - 释放库存
  
  pending → cancelled:
    触发: 超时 15 分钟
    动作:
      - 更新订单状态
      - 记录 cancelled_at
      - 释放库存

订单约束:
  - MUST 包含钱包地址
  - MUST 包含幂等键
  - MUST 关联站点
  - MUST 记录价格快照
  - MAY 关联推荐人
```

### 3.3 代币分配生命周期

```yaml
分配状态定义:
  pending:
    描述: 等待发放
    可转换至: [processing]
    触发: 订单支付成功自动创建
  
  processing:
    描述: 发放中
    可转换至: [completed, failed]
    触发: 管理员点击"发放"
  
  completed:
    描述: 已完成
    可转换至: []
    终态: true
  
  failed:
    描述: 发放失败
    可转换至: [pending]
    可重试: true

分配规则:
  - MUST 一个订单一条分配记录
  - MUST 记录 Fireblocks 交易 ID
  - MUST 记录链上交易哈希
  - MUST 支持失败重试
  - MUST 批量发放最多 100 笔
```

### 3.4 佣金生命周期

```yaml
佣金状态定义:
  hold:
    描述: 冻结期
    可转换至: [ready, cancelled]
    期限: 可配置（默认 7 天）
  
  ready:
    描述: 可结算
    可转换至: [paid, cancelled]
    触发: 冻结期结束
  
  paid:
    描述: 已结算
    可转换至: []
    终态: true
  
  cancelled:
    描述: 已取消
    可转换至: []
    终态: true

佣金规则:
  - MUST 支持多层级（默认 2 层）
  - MUST 可按站点配置
  - MUST 可按代理自定义
  - MUST 记录佣金来源（订单/层级）
  - MUST 支持冻结期
  - MUST 使用唯一约束防重复
```

---

## 4. 技术架构规则

### 4.1 架构原则

```yaml
原则 1: 微服务优先
  - SHOULD 按业务域拆分服务
  - MUST 服务间通过 API 通信
  - MUST 避免直接数据库访问

原则 2: 无状态设计
  - MUST API 无状态
  - MUST Session 存储在 Redis
  - MUST 支持水平扩展

原则 3: 异步优先
  - SHOULD 长时间任务异步执行
  - MUST Webhook 处理异步
  - MUST 使用消息队列解耦

原则 4: 容错设计
  - MUST 实现重试机制
  - MUST 实现熔断机制
  - MUST 实现降级策略
  - MUST 记录所有错误
```

### 4.2 技术栈规范

```yaml
后端技术栈:
  语言: Python 3.11+
  框架: Django 4.2+ / Django REST Framework
  数据库: PostgreSQL 15+
  缓存: Redis 7+
  任务队列: Celery + Redis
  Web 服务器: Gunicorn + Nginx
  
前端技术栈:
  框架: Next.js 14+ (App Router)
  语言: TypeScript 5+
  状态管理: React Context / Zustand
  UI 库: Tailwind CSS + shadcn/ui
  钱包集成: @web3modal/wagmi

第三方服务:
  认证: Auth0
  支付: Stripe
  代币托管: Fireblocks
  钱包连接: WalletConnect
  监控: Sentry
  日志: CloudWatch / ELK
```

### 4.3 代码组织规范

```yaml
后端目录结构:
  posx-backend/
    ├── apps/                    # 应用模块
    │   ├── users/              # 用户模块
    │   ├── sites/              # 站点模块
    │   ├── tiers/              # 档位模块
    │   ├── orders/             # 订单模块
    │   ├── allocations/        # 分配模块
    │   ├── commissions/        # 佣金模块
    │   ├── webhooks/           # Webhook 模块
    │   └── core/               # 核心模块
    ├── config/                 # 配置
    │   ├── settings/           # Django 配置
    │   ├── celery.py          # Celery 配置
    │   └── urls.py            # URL 路由
    ├── middleware/             # 中间件
    ├── utils/                  # 工具函数
    ├── tests/                  # 测试
    └── manage.py

前端目录结构:
  posx-frontend/
    ├── app/                    # Next.js App Router
    │   ├── (auth)/            # 认证相关页面
    │   ├── (dashboard)/       # 用户仪表板
    │   ├── (admin)/           # 管理后台
    │   └── api/               # API 路由
    ├── components/             # 组件
    │   ├── ui/                # 基础 UI 组件
    │   ├── forms/             # 表单组件
    │   └── features/          # 功能组件
    ├── lib/                    # 工具库
    │   ├── api/               # API 客户端
    │   ├── auth/              # 认证逻辑
    │   └── wallet/            # 钱包逻辑
    ├── hooks/                  # React Hooks
    ├── types/                  # TypeScript 类型
    └── public/                 # 静态资源

模块划分原则:
  - MUST 按业务域划分模块
  - MUST 模块间低耦合
  - SHOULD 模块内高内聚
  - MUST 避免循环依赖
```

### 4.4 数据库架构规范

```yaml
数据库选择:
  主库: PostgreSQL 15+
  理由:
    - ACID 事务支持
    - 丰富的数据类型
    - 强大的索引能力
    - JSON 支持

表设计原则:
  - MUST 使用 UUID 作为主键
  - MUST 所有表包含 created_at
  - SHOULD 所有表包含 updated_at
  - MUST 使用 TIMESTAMPTZ 存储时间
  - MUST 金额使用 NUMERIC(18, 6)
  - MUST 外键使用 ON DELETE 策略

索引规范:
  - MUST 主键自动索引
  - MUST 外键创建索引
  - MUST 查询条件字段创建索引
  - SHOULD 复合索引优先于单列索引
  - MUST 定期分析索引使用率

约束规范:
  - MUST 使用 UNIQUE 约束防重
  - MUST 使用 CHECK 约束验证数据
  - MUST 使用 NOT NULL 约束必填字段
  - SHOULD 使用触发器同步冗余字段
```

---

## 5. 数据模型规范

### 5.1 核心实体定义

```yaml
User（用户）:
  主键: user_id (UUID)
  唯一键:
    - auth0_sub
    - wallet_address
    - email
    - referral_code
  索引:
    - referrer_id
    - primary_wallet_id
  必填字段:
    - user_id
    - auth_type
    - referral_code
    - created_at
  可选字段:
    - auth0_sub (auth_type=auth0 时必填)
    - wallet_address (auth_type=wallet 时必填)
    - email
    - primary_wallet_id
    - is_agent
    - stripe_account_id

Wallet（钱包）:
  主键: wallet_id (UUID)
  唯一键:
    - (user_id, address)
    - LOWER(address)
  索引:
    - user_id
    - address
    - LOWER(address)
  约束:
    - address 格式: ^0x[a-fA-F0-9]{40}$
    - 每个用户最多一个主钱包
  必填字段:
    - wallet_id
    - user_id
    - address
    - created_at

Site（站点）:
  主键: site_id (UUID)
  唯一键: code
  必填字段:
    - site_id
    - code
    - name
    - currency_code
    - is_active
    - created_at

Tier（档位）:
  主键: tier_id (UUID)
  索引:
    - site_id
    - (site_id, display_order)
  必填字段:
    - tier_id
    - site_id
    - name
    - list_price_usd
    - tokens_per_unit
    - total_units
    - sold_units
    - available_units
    - version (乐观锁)
    - is_active
    - created_at

Order（订单）:
  主键: order_id (UUID)
  唯一键:
    - stripe_payment_intent_id
    - idempotency_key
  索引:
    - buyer_id
    - site_id
    - referrer_id
    - status
    - created_at
    - disputed
  必填字段:
    - order_id
    - buyer_id
    - site_id
    - status
    - list_price_usd
    - final_price_usd
    - wallet_address
    - created_at

Allocation（分配）:
  主键: allocation_id (UUID)
  唯一键: order_id
  索引:
    - order_id
    - status
    - fireblocks_tx_id
  必填字段:
    - allocation_id
    - order_id
    - wallet_address
    - token_amount
    - status
    - created_at

Commission（佣金）:
  主键: commission_id (UUID)
  唯一键: (order_id, agent_id, level)
  索引:
    - order_id
    - agent_id
    - status
  必填字段:
    - commission_id
    - order_id
    - agent_id
    - level
    - rate_percent
    - commission_amount_usd
    - status
    - hold_until
    - created_at
```

### 5.2 数据完整性规则

```yaml
外键策略:
  用户删除:
    - orders.buyer_id: ON DELETE PROTECT (禁止删除有订单的用户)
    - commissions.agent_id: ON DELETE PROTECT
    - wallets.user_id: ON DELETE CASCADE
  
  站点删除:
    - tiers.site_id: ON DELETE PROTECT
    - orders.site_id: ON DELETE PROTECT
  
  订单删除:
    - allocations.order_id: ON DELETE CASCADE
    - commissions.order_id: ON DELETE CASCADE

唯一性约束:
  - users.auth0_sub
  - users.wallet_address
  - users.email
  - users.referral_code
  - wallets.address (LOWER)
  - sites.code
  - tiers.tier_id
  - orders.stripe_payment_intent_id
  - orders.idempotency_key
  - allocations.order_id
  - commissions.(order_id, agent_id, level)
  - webhooks.(source, external_event_id)
  - nonces.nonce

检查约束:
  - users.auth_type IN ('auth0', 'wallet')
  - orders.status IN ('pending', 'paid', 'failed', 'cancelled')
  - orders.wallet_address ~ '^0x[a-fA-F0-9]{40}$'
  - allocations.status IN ('pending', 'processing', 'completed', 'failed')
  - commissions.status IN ('hold', 'ready', 'paid', 'cancelled')
  - commissions.rate_percent >= 0 AND <= 100
```

### 5.3 数据迁移规范

```yaml
迁移原则:
  - MUST 所有变更通过迁移脚本
  - MUST 迁移脚本可回滚
  - MUST 迁移前备份数据
  - MUST 在非高峰期执行
  - SHOULD 分阶段执行大迁移

迁移命名:
  格式: YYYYMMDD_HHMM_description
  示例: 20251107_1430_add_wallet_nonces_table

迁移内容:
  - DDL 变更（表、字段、索引）
  - 数据迁移
  - 约束变更
  - 触发器/函数变更

回滚策略:
  - MUST 提供回滚脚本
  - MUST 测试回滚流程
  - SHOULD 记录回滚影响
```

---

## 6. API 设计规范

### 6.1 RESTful 规范

```yaml
URL 命名规则:
  - MUST 使用小写字母
  - MUST 使用连字符分隔
  - MUST 使用复数名词
  - MUST_NOT 在 URL 中包含动词

  正确示例:
    GET    /api/v1/users
    GET    /api/v1/users/{user_id}
    POST   /api/v1/orders
    PUT    /api/v1/orders/{order_id}
    DELETE /api/v1/wallets/{wallet_id}
  
  错误示例:
    GET    /api/v1/getUsers
    POST   /api/v1/createOrder
    GET    /api/v1/user_list

HTTP 方法规范:
  GET:
    用途: 查询资源
    幂等: 是
    缓存: 可以
  
  POST:
    用途: 创建资源
    幂等: 否（需实现）
    缓存: 否
  
  PUT:
    用途: 完整更新资源
    幂等: 是
    缓存: 否
  
  PATCH:
    用途: 部分更新资源
    幂等: 是
    缓存: 否
  
  DELETE:
    用途: 删除资源
    幂等: 是
    缓存: 否

版本控制:
  策略: URL 路径版本
  格式: /api/v{major}/
  示例: /api/v1/users
  
  版本升级规则:
    - 新增字段: 不升级
    - 删除字段: 升级
    - 修改字段类型: 升级
    - 修改响应结构: 升级
```

### 6.2 请求规范

```yaml
请求头规范:
  必需:
    Content-Type: application/json
    Authorization: Bearer {token}
  
  可选:
    X-Site-Code: 站点代码 (默认 NA)
    X-Idempotency-Key: 幂等键 (POST 请求推荐)
    Accept-Language: 语言偏好

请求体规范:
  格式: JSON
  编码: UTF-8
  
  字段命名:
    - MUST 使用 snake_case
    - MUST 使用有意义的名称
    - SHOULD 避免缩写
  
  日期格式:
    - MUST 使用 ISO 8601
    - 示例: 2025-11-07T14:30:00Z
  
  金额格式:
    - MUST 使用字符串
    - MUST 包含小数点
    - 示例: "1000.50"
  
  布尔值:
    - MUST 使用 true/false
    - MUST_NOT 使用 1/0

幂等性实现:
  - MUST POST 请求支持幂等键
  - MUST 幂等键唯一
  - MUST 相同幂等键返回相同结果
  - SHOULD 幂等键保留 48 小时
```

### 6.3 响应规范

```yaml
响应格式:
  成功响应:
    结构:
      {
        "data": {},
        "meta": {
          "request_id": "uuid",
          "timestamp": "2025-11-07T14:30:00Z"
        }
      }
  
  错误响应:
    结构:
      {
        "error": {
          "code": "ERROR_CODE",
          "message": "Human readable message",
          "details": {}
        },
        "meta": {
          "request_id": "uuid",
          "timestamp": "2025-11-07T14:30:00Z"
        }
      }

HTTP 状态码规范:
  2xx 成功:
    200: OK (查询成功)
    201: Created (创建成功)
    204: No Content (删除成功)
  
  4xx 客户端错误:
    400: Bad Request (请求参数错误)
    401: Unauthorized (未认证)
    403: Forbidden (无权限)
    404: Not Found (资源不存在)
    409: Conflict (资源冲突)
    422: Unprocessable Entity (业务逻辑错误)
    429: Too Many Requests (限流)
  
  5xx 服务端错误:
    500: Internal Server Error (服务器错误)
    503: Service Unavailable (服务不可用)

错误码规范:
  格式: {MODULE}_{ERROR_TYPE}_{DETAIL}
  
  示例:
    USER_NOT_FOUND: 用户不存在
    ORDER_INSUFFICIENT_STOCK: 库存不足
    PAYMENT_FAILED: 支付失败
    WALLET_ADDRESS_INVALID: 钱包地址无效
    NONCE_EXPIRED: Nonce 已过期

分页规范:
  查询参数:
    page: 页码 (从 1 开始)
    page_size: 每页数量 (默认 20，最大 100)
  
  响应结构:
    {
      "data": [],
      "meta": {
        "page": 1,
        "page_size": 20,
        "total": 100,
        "total_pages": 5
      }
    }
```

### 6.4 核心 API 端点

```yaml
认证相关:
  POST   /api/v1/auth/nonce                # 生成 Nonce
  POST   /api/v1/auth/wallet-login         # 钱包登录
  POST   /api/v1/auth/wallet-bind          # 绑定钱包
  DELETE /api/v1/auth/wallet-unbind        # 解绑钱包
  POST   /api/v1/auth/logout               # 登出

用户相关:
  GET    /api/v1/users/me                  # 获取当前用户
  PATCH  /api/v1/users/me                  # 更新当前用户
  GET    /api/v1/users/me/token-balance    # 获取代币余额
  GET    /api/v1/users/me/orders           # 获取订单列表
  GET    /api/v1/users/me/commissions      # 获取佣金列表

钱包相关:
  GET    /api/v1/wallets                   # 获取钱包列表
  POST   /api/v1/wallets                   # 添加钱包
  PUT    /api/v1/wallets/{id}/set-primary  # 设置主钱包
  DELETE /api/v1/wallets/{id}              # 删除钱包

站点相关:
  GET    /api/v1/sites                     # 获取站点列表
  GET    /api/v1/sites/{code}              # 获取站点详情

档位相关:
  GET    /api/v1/tiers                     # 获取档位列表
  GET    /api/v1/tiers/{id}                # 获取档位详情

订单相关:
  POST   /api/v1/orders                    # 创建订单
  GET    /api/v1/orders/{id}               # 获取订单详情
  GET    /api/v1/orders                    # 获取订单列表

Webhook:
  POST   /api/v1/webhooks/stripe           # Stripe Webhook
  POST   /api/v1/webhooks/fireblocks       # Fireblocks Webhook

管理员 API:
  GET    /api/v1/admin/allocations         # 获取待发放列表
  POST   /api/v1/admin/allocations/batch   # 批量发放
  POST   /api/v1/admin/allocations/{id}/retry  # 重试发放
  GET    /api/v1/admin/orders              # 订单管理
  GET    /api/v1/admin/commissions         # 佣金管理
  POST   /api/v1/admin/commissions/settle  # 佣金结算
```

---

## 7. 认证与授权规范

### 7.1 认证方式

```yaml
支持的认证方式:
  1. Auth0 传统登录:
     类型: Email + Password
     实现: @auth0/nextjs-auth0
     Token: Auth0 JWT
     
  2. Auth0 Passkey:
     类型: WebAuthn / FIDO2
     实现: Auth0 Passwordless
     Token: Auth0 JWT
     
  3. WalletConnect:
     类型: Web3 钱包签名
     实现: @web3modal/wagmi + SIWE
     Token: Auth0 JWT (推荐) 或 自签发 JWT

JWT 规范:
  算法: RS256 (Auth0) 或 HS256 (自签发)
  过期时间: 24 小时
  刷新策略: Refresh Token (Auth0)
  
  Payload 必含:
    sub: 用户唯一标识
    iss: 签发者
    aud: 受众
    exp: 过期时间
    iat: 签发时间
    
  Payload 扩展 (自定义声明):
    https://posx.io/user_id: 用户 ID
    https://posx.io/roles: 角色列表
    https://posx.io/permissions: 权限列表
```

### 7.2 Nonce 安全规范

```yaml
Nonce 生成规则:
  - MUST 使用密码学安全随机数
  - MUST 长度至少 32 字节
  - MUST 关联钱包地址
  - MUST 设置过期时间（5 分钟）

Nonce 验证规则:
  - MUST 验证 Nonce 存在
  - MUST 验证未过期
  - MUST 验证未使用
  - MUST 验证钱包地址匹配
  - MUST 使用后标记为已用

Nonce 存储:
  - MUST 存储在数据库
  - MUST 记录创建时间
  - MUST 记录过期时间
  - SHOULD 记录 IP 地址（脱敏）
  - SHOULD 记录 User-Agent（截断）

Nonce 清理:
  - MUST 定期清理过期 Nonce
  - SHOULD 每小时执行一次
```

### 7.3 权限模型

```yaml
角色定义:
  user:
    描述: 普通用户
    权限:
      - orders:read (自己的订单)
      - orders:write (创建订单)
      - wallets:read (自己的钱包)
      - wallets:write (管理钱包)
      - commissions:read (自己的佣金)
  
  agent:
    描述: 代理
    继承: user
    额外权限:
      - commissions:read (下级佣金)
      - referrals:read (下级用户)
  
  admin:
    描述: 管理员
    权限:
      - *:* (所有权限)

权限检查:
  位置: 中间件 + 视图装饰器
  策略: RBAC (基于角色)
  实现: 
    - 后端: Django Permission 或 JWT Claims
    - 前端: 基于角色显示/隐藏组件
```

---

## 8. 支付与订单规范

### 8.1 Stripe 集成规范

```yaml
Stripe 配置:
  API 版本: 2024-11-20.acacia
  密钥类型: Secret Key (后端) + Publishable Key (前端)
  测试模式: 使用 test_ 密钥
  生产模式: 使用 live_ 密钥

Payment Intent 创建:
  参数:
    amount: 金额（美分）
    currency: usd
    payment_method_types: [card]
    metadata:
      order_id: 订单 ID
      site_code: 站点代码
      user_id: 用户 ID
      wallet_address: 钱包地址

Webhook 订阅事件:
  1. payment_intent.succeeded:
     触发: 支付成功
     动作:
       - 更新订单状态 → paid
       - 记录 paid_at
       - 生成佣金
       - 创建分配记录
  
  2. payment_intent.payment_failed:
     触发: 支付失败
     动作:
       - 更新订单状态 → failed
       - 记录失败原因
       - 释放库存
  
  3. charge.dispute.created:
     触发: 银行拒付/争议
     动作:
       - 标记订单 disputed=true
       - 记录争议信息
       - 发送告警通知
       - 不改变订单状态

Webhook 安全:
  - MUST 验证签名 (Stripe-Signature header)
  - MUST 使用 Webhook Secret
  - MUST 幂等处理（唯一约束）
  - MUST 快速返回 200
  - MUST 异步处理业务逻辑
  - MUST 记录所有 Webhook 日志
```

### 8.2 订单创建规范

```yaml
前置条件检查:
  - MUST 用户已登录
  - MUST 用户有主钱包地址
  - MUST 钱包地址已验证
  - MUST 档位库存充足
  - MUST 提供幂等键

订单创建流程:
  1. 验证幂等键:
     - 检查是否已存在
     - 存在则返回既有订单
  
  2. 验证钱包地址:
     - 检查 user.primary_wallet_id
     - 验证地址格式
     - 不存在返回 WALLET_ADDRESS_REQUIRED
  
  3. 锁定库存:
     - 使用 SELECT FOR UPDATE
     - 检查 available_units >= quantity
     - 更新 sold_units += quantity
     - 更新 version += 1
  
  4. 计算价格:
     - list_price = tier.list_price_usd * quantity
     - 应用折扣（取较大值）
     - final_price = list_price * (1 - discount/100)
  
  5. 创建订单记录:
     - 生成 order_id
     - status = pending
     - 记录钱包地址
     - 记录价格
     - 设置过期时间 (created_at + 15 min)
  
  6. 创建 Stripe Payment Intent:
     - 调用 Stripe API
     - 记录 payment_intent_id
     - 返回 client_secret
  
  7. 记录幂等键:
     - 关联 order_id
     - 记录响应体

订单超时取消:
  - MUST 定期扫描（每 5 分钟）
  - 条件: status=pending AND created_at < now() - 15min
  - 动作:
    - 更新 status → cancelled
    - 记录 cancelled_at
    - 释放库存
```

### 8.3 库存控制规范

```yaml
库存字段:
  total_units: 总库存（不变）
  sold_units: 已售出（递增）
  available_units: 可用库存 (total - sold)
  version: 版本号（乐观锁）

乐观锁实现:
  更新 SQL:
    UPDATE tiers
    SET sold_units = sold_units + {quantity},
        version = version + 1
    WHERE tier_id = {id}
      AND version = {expected_version}
      AND available_units >= {quantity}
  
  检查:
    IF affected_rows = 0 THEN
      RAISE InsufficientStockError
    END IF

并发控制:
  - MUST 使用数据库事务
  - MUST 使用 SELECT FOR UPDATE 锁定
  - MUST 使用版本号乐观锁
  - MUST 捕获并发冲突异常
  - SHOULD 实现重试机制（最多 3 次）
```

---

## 9. 代币分配规范

### 9.1 Fireblocks 集成规范

```yaml
Fireblocks 配置:
  认证方式: API Key + RSA Private Key
  API Base URL: https://api.fireblocks.io
  Vault Account: 主账户 ID
  Asset ID: 代币资产 ID (如 ETH_TEST)

API Key 生成:
  位置: Fireblocks Console → Settings → API Users
  类型: Admin 或 Editor
  权限: Transaction Signing

Private Key 生成:
  算法: RSA 4096
  格式: PEM
  存储: 环境变量（加密）

发币流程:
  1. 管理员选择待发放批次:
     - 查询 allocations (status=pending)
     - 最多选择 100 笔
  
  2. 调用 Fireblocks API:
     - endpoint: /v1/transactions
     - method: POST
     - 参数:
       assetId: 资产 ID
       source: Vault Account
       destination: 用户钱包地址
       amount: 代币数量
       note: 订单备注
  
  3. 更新分配状态:
     - status → processing
     - 记录 fireblocks_tx_id
     - 记录 processing_at
  
  4. 等待 Fireblocks 回调:
     - 接收 Webhook
     - 验证签名
     - 更新状态
  
  5. 最终状态:
     - completed: 记录 tx_hash, confirmed_at
     - failed: 记录 failure_reason

批量发放限制:
  - MUST 最多 100 笔/批次
  - SHOULD 控制发放频率（避免触发限流）
  - MUST 记录所有失败原因
  - MUST 支持失败重试
```

### 9.2 Fireblocks Webhook 规范

```yaml
Webhook 配置:
  URL: https://api.posx.io/api/v1/webhooks/fireblocks
  Events:
    - TRANSACTION_STATUS_UPDATED

签名验证:
  算法: RSA-SHA512
  Header: X-Fireblocks-Signature
  公钥来源: Fireblocks Console

  验证步骤:
    1. 获取签名 Header
    2. 加载 Fireblocks 公钥
    3. 使用 RSA-SHA512 验证
    4. 验证失败返回 403

事件处理:
  TRANSACTION_STATUS_UPDATED:
    COMPLETED:
      - 更新 allocation.status → completed
      - 记录 tx_hash
      - 记录 confirmed_at
    
    FAILED:
      - 更新 allocation.status → failed
      - 记录 failure_reason
    
    CANCELLED:
      - 更新 allocation.status → failed
      - 记录 failure_reason

幂等性保证:
  - MUST 使用唯一约束 (source, external_event_id)
  - MUST 快速返回 200
  - MUST 异步处理业务逻辑
```

### 9.3 代币余额显示规范

```yaml
数据来源:
  总购买量:
    来源: 本地数据库
    计算: SUM(orders.quantity * tier.tokens_per_unit)
    条件: orders.status = 'paid'
  
  已发放量:
    来源: Fireblocks API
    接口: /v1/vault/accounts/{id}/assets/{asset_id}
    字段: total
  
  锁仓量:
    来源: Fireblocks API
    接口: /v1/vault/accounts/{id}/vesting
    字段: locked_amount
  
  可用量:
    计算: total - locked
  
  解锁时间表:
    来源: Fireblocks Vesting 配置
    格式: [{date, amount}, ...]

查询频率:
  - SHOULD 缓存 5 分钟
  - SHOULD 后台定期同步
  - MAY 用户主动刷新

显示规则:
  - MUST 显示所有四个指标
  - MUST 显示解锁时间表
  - SHOULD 显示单位（POSX）
  - SHOULD 格式化大数字
```

---

## 10. 佣金系统规范

### 10.1 佣金配置规范

```yaml
配置层级:
  1. 站点默认配置:
     范围: 整个站点
     优先级: 最低
     示例: NA 站点默认 2 层（12%, 4%）
  
  2. 代理自定义配置:
     范围: 特定代理
     优先级: 最高
     示例: VIP 代理 3 层（15%, 6%, 3%）

配置参数:
  config_name: 配置名称
  levels: 层级配置列表
    - level: 层级（1, 2, 3...）
    - rate_percent: 佣金比例
    - max_amount_usd: 单笔最大金额（可选）
    - min_amount_usd: 单笔最小金额（可选）
    - is_enabled: 是否启用
  
  rules: 特殊规则（可选）
    - rule_type: 规则类型（sunline/tiered/capped）
    - rule_config: 规则配置（JSON）

配置生效规则:
  1. 查询代理是否有自定义配置
  2. 有则使用代理配置
  3. 无则使用站点默认配置
  4. 按生效时间范围匹配
```

### 10.2 佣金计算规范

```yaml
计算触发:
  时机: 订单支付成功后
  输入:
    - order_id: 订单 ID
    - order_amount: 订单金额
    - buyer_id: 购买者 ID
    - site_id: 站点 ID

计算流程:
  1. 获取佣金配置:
     - 查询购买者的推荐人
     - 递归向上查找 N 层
     - 获取每层代理的配置
  
  2. 计算每层佣金:
     FOR level IN 1..N:
       agent = get_agent_at_level(level)
       IF agent IS NULL: BREAK
       
       config = get_commission_config(agent, site_id)
       level_config = config.levels[level]
       
       IF NOT level_config.is_enabled: CONTINUE
       
       rate = level_config.rate_percent
       amount = order_amount * rate / 100
       
       # 应用金额限制
       IF max_amount IS NOT NULL:
         amount = MIN(amount, max_amount)
       IF min_amount IS NOT NULL AND amount < min_amount:
         SKIP
       
       # 创建佣金记录
       CREATE commission:
         order_id: order_id
         agent_id: agent.user_id
         level: level
         rate_percent: rate
         commission_amount_usd: amount
         status: 'hold'
         hold_until: now() + hold_period
  
  3. 应用特殊规则:
     - 太阳线规则: 同一订单只计算一次
     - 封顶规则: 单日/单月佣金上限
     - 阶梯规则: 根据业绩调整比例

唯一性保证:
  - MUST 使用唯一约束 (order_id, agent_id, level)
  - MUST 避免重复计算
  - MUST 事务内完成
```

### 10.3 佣金结算规范

```yaml
冻结期规则:
  默认: 7 天
  可配置: 按站点或代理
  目的: 防止退款/拒付（虽然无退款，但保留机制）

状态转换:
  hold → ready:
    触发: 定时任务（每小时）
    条件: hold_until <= now()
    动作: 更新 status = 'ready'
  
  ready → paid:
    触发: 管理员结算
    条件: status = 'ready'
    动作:
      - 更新 status = 'paid'
      - 记录 paid_at
      - 转账到代理账户（Stripe Connect）
  
  * → cancelled:
    触发: 订单取消
    条件: order.status = 'cancelled'
    动作: 更新 status = 'cancelled'

结算方式:
  1. 手动结算:
     - 管理员选择代理
     - 查看可结算佣金
     - 确认结算
     - 调用 Stripe Transfer API
  
  2. 自动结算（可选）:
     - 定时任务（每周/每月）
     - 自动结算所有 ready 状态
     - 发送结算通知

结算记录:
  - MUST 记录结算批次
  - MUST 记录转账详情
  - MUST 可追溯到订单
  - SHOULD 生成结算报表
```

---

## 11. 安全规范

### 11.1 数据安全

```yaml
敏感数据保护:
  加密存储:
    - Fireblocks Private Key (环境变量加密)
    - Stripe Secret Key (环境变量加密)
    - 数据库连接字符串（加密）
  
  传输加密:
    - MUST 使用 HTTPS/TLS 1.3
    - MUST 使用有效证书
    - MUST_NOT 使用自签名证书（生产）
  
  访问控制:
    - MUST 最小权限原则
    - MUST 定期审计权限
    - SHOULD 使用 IAM 角色

数据脱敏:
  日志记录:
    - MUST_NOT 记录密码
    - MUST_NOT 记录完整信用卡号
    - SHOULD 脱敏钱包地址（仅显示前 6 后 4 位）
    - SHOULD 脱敏 IP 地址
    - SHOULD 脱敏 User-Agent（截断）
  
  数据导出:
    - MUST 脱敏敏感字段
    - MUST 记录导出日志
    - SHOULD 限制导出频率

备份策略:
  数据库:
    - MUST 每日全量备份
    - MUST 每小时增量备份
    - MUST 异地存储
    - MUST 加密备份文件
    - MUST 定期测试恢复
  
  保留期限:
    - 全量备份: 30 天
    - 增量备份: 7 天
    - 归档数据: 7 年（根据合规要求）
```

### 11.2 API 安全

```yaml
认证安全:
  - MUST 所有 API 需要认证（除公开端点）
  - MUST 验证 JWT 签名
  - MUST 检查 JWT 过期时间
  - MUST 验证 JWT audience
  - SHOULD 实现 Token 黑名单（可选）

授权安全:
  - MUST 验证用户权限
  - MUST 验证资源所有权
  - MUST 实现 RBAC
  - SHOULD 记录权限检查日志

输入验证:
  - MUST 验证所有输入参数
  - MUST 使用白名单验证
  - MUST 验证数据类型
  - MUST 验证数据范围
  - MUST 防止 SQL 注入
  - MUST 防止 XSS 攻击
  - MUST 防止 CSRF 攻击

输出编码:
  - MUST 转义 HTML 输出
  - MUST 转义 SQL 参数
  - MUST 转义 JSON 输出
  - SHOULD 使用 ORM/框架内置方法

限流策略:
  全局限流:
    - 1000 req/min per IP
    - 10000 req/hour per IP
  
  API 限流:
    - 登录: 5 req/min per IP
    - 创建订单: 10 req/min per user
    - 钱包登录: 3 req/min per wallet
  
  实现:
    - SHOULD 使用 Redis
    - SHOULD 返回 429 状态码
    - SHOULD 包含 Retry-After header
```

### 11.3 Webhook 安全

```yaml
Stripe Webhook:
  验证方式: HMAC-SHA256
  签名 Header: Stripe-Signature
  验证库: stripe.webhook.construct_event
  
  安全措施:
    - MUST 验证签名
    - MUST 使用 Webhook Secret
    - MUST 记录所有请求
    - MUST 幂等处理
    - SHOULD 限制来源 IP

Fireblocks Webhook:
  验证方式: RSA-SHA512
  签名 Header: X-Fireblocks-Signature
  公钥来源: Fireblocks Console
  
  验证步骤:
    1. 解析签名 Header (Base64)
    2. 加载公钥 (PEM 格式)
    3. 验证签名:
       public_key.verify(
         signature,
         payload,
         padding.PKCS1v15(),
         hashes.SHA512()
       )
    4. 验证失败返回 403
  
  安全措施:
    - MUST 验证签名
    - MUST 记录所有请求
    - MUST 幂等处理
    - SHOULD 限制来源 IP

通用规则:
  - MUST 快速返回 200
  - MUST 异步处理业务逻辑
  - MUST 记录处理结果
  - MUST 实现重试机制
  - SHOULD 告警异常事件
```

---

## 12. 环境配置规范

### 12.1 环境定义

```yaml
环境类型:
  local:
    用途: 本地开发
    数据: 开发数据 / Mock 数据
    外部服务: 测试环境或 Mock
    日志级别: DEBUG
  
  demo:
    用途: 演示 / 用户验收测试
    数据: 演示数据 / 真实测试数据
    外部服务: 测试环境
    日志级别: INFO
    域名: demo.posx.io
  
  production:
    用途: 生产环境
    数据: 真实生产数据
    外部服务: 生产环境
    日志级别: WARNING
    域名: posx.io

环境隔离:
  - MUST 物理隔离（不同服务器/集群）
  - MUST 数据隔离（不同数据库）
  - MUST 密钥隔离（不同 API Key）
  - SHOULD 网络隔离（VPC）
```

### 12.2 本地开发环境

```yaml
系统要求:
  操作系统: macOS / Linux / Windows (WSL2)
  Docker: 20.10+
  Docker Compose: 2.0+
  Python: 3.11+
  Node.js: 20+
  Git: 2.30+

必需服务:
  - PostgreSQL 15 (Docker)
  - Redis 7 (Docker)
  - Backend API (Django)
  - Frontend (Next.js)
  - Celery Worker (可选)
  - Celery Beat (可选)

环境变量 (Backend):
  # Django
  DJANGO_ENV=local
  DEBUG=true
  SECRET_KEY=<random-string>
  ALLOWED_HOSTS=localhost,127.0.0.1
  
  # Database
  DATABASE_URL=postgresql://posx:posx@localhost:5432/posx_local
  
  # Redis
  REDIS_URL=redis://localhost:6379/0
  CELERY_BROKER_URL=redis://localhost:6379/0
  
  # Auth0
  AUTH0_DOMAIN=dev-xxx.auth0.com
  AUTH0_AUDIENCE=https://api.posx.local
  AUTH0_ISSUER=https://dev-xxx.auth0.com/
  AUTH0_M2M_CLIENT_ID=xxx
  AUTH0_M2M_CLIENT_SECRET=xxx
  
  # Stripe (测试密钥)
  STRIPE_SECRET_KEY=sk_test_xxx
  STRIPE_PUBLISHABLE_KEY=pk_test_xxx
  STRIPE_WEBHOOK_SECRET=whsec_xxx
  
  # Fireblocks (测试环境)
  FIREBLOCKS_API_KEY=xxx
  FIREBLOCKS_PRIVATE_KEY=<pem-content>
  FIREBLOCKS_BASE_URL=https://sandbox-api.fireblocks.io
  FIREBLOCKS_VAULT_ACCOUNT_ID=0
  FIREBLOCKS_ASSET_ID=ETH_TEST
  FIREBLOCKS_WEBHOOK_PUBLIC_KEY=<pem-content>
  
  # Blockchain (测试网)
  ETH_RPC_URL=https://sepolia.infura.io/v3/xxx
  TOKEN_CONTRACT_ADDRESS=0x...
  
  # 其他
  FRONTEND_URL=http://localhost:3000
  CORS_ALLOWED_ORIGINS=http://localhost:3000
  ALLOWED_SITE_CODES=NA,ASIA
  NONCE_TTL_MINUTES=5
  IDEMPOTENCY_KEY_RETENTION_HOURS=48

环境变量 (Frontend):
  # Auth0
  AUTH0_BASE_URL=http://localhost:3000
  AUTH0_ISSUER_BASE_URL=https://dev-xxx.auth0.com
  AUTH0_CLIENT_ID=xxx
  AUTH0_CLIENT_SECRET=xxx
  AUTH0_SECRET=<random-string>
  
  # API
  NEXT_PUBLIC_API_URL=http://localhost:8000/api
  
  # Stripe
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_xxx
  
  # WalletConnect
  NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=xxx
  
  # Blockchain
  NEXT_PUBLIC_ETH_RPC_URL=https://sepolia.infura.io/v3/xxx
  NEXT_PUBLIC_TOKEN_CONTRACT_ADDRESS=0x...
  
  # Site
  NEXT_PUBLIC_SITE_CODE=NA

启动命令:
  # 启动基础服务
  docker-compose up -d postgres redis
  
  # 启动后端
  cd backend
  python manage.py migrate
  python manage.py runserver
  
  # 启动前端
  cd frontend
  npm install
  npm run dev
  
  # 启动 Celery（可选）
  celery -A config worker -l info
  celery -A config beat -l info
```

### 12.3 Demo 环境

```yaml
部署方式: Docker + Docker Compose

服务器要求:
  CPU: 4 核
  内存: 8 GB
  磁盘: 100 GB SSD
  操作系统: Ubuntu 22.04 LTS

Docker 服务:
  - postgres:15-alpine
  - redis:7-alpine
  - backend:demo (Django)
  - frontend:demo (Next.js)
  - nginx:alpine (反向代理)
  - celery-worker:demo
  - celery-beat:demo

环境变量 (Backend):
  # Django
  DJANGO_ENV=demo
  DEBUG=false
  SECRET_KEY=<secure-random-string>
  ALLOWED_HOSTS=demo.posx.io,api.demo.posx.io
  
  # Database
  DATABASE_URL=postgresql://posx:xxx@postgres:5432/posx_demo
  
  # Redis
  REDIS_URL=redis://redis:6379/0
  
  # Auth0
  AUTH0_DOMAIN=demo-xxx.auth0.com
  AUTH0_AUDIENCE=https://api.demo.posx.io
  
  # Stripe (测试密钥)
  STRIPE_SECRET_KEY=sk_test_xxx
  STRIPE_WEBHOOK_SECRET=whsec_xxx
  
  # Fireblocks (测试环境)
  FIREBLOCKS_API_KEY=xxx
  FIREBLOCKS_BASE_URL=https://sandbox-api.fireblocks.io
  
  # Sentry
  SENTRY_DSN=https://xxx@sentry.io/xxx
  SENTRY_ENVIRONMENT=demo
  
  # 其他
  FRONTEND_URL=https://demo.posx.io
  CORS_ALLOWED_ORIGINS=https://demo.posx.io

环境变量 (Frontend):
  # Auth0
  AUTH0_BASE_URL=https://demo.posx.io
  AUTH0_ISSUER_BASE_URL=https://demo-xxx.auth0.com
  
  # API
  NEXT_PUBLIC_API_URL=https://api.demo.posx.io/api
  
  # 其他同本地环境

域名配置:
  demo.posx.io → Frontend
  api.demo.posx.io → Backend
  
SSL 证书:
  提供商: Let's Encrypt
  自动续期: Certbot

备份策略:
  数据库: 每日 1 次（保留 7 天）
  文件: 无需备份（可重建）
```

### 12.4 生产环境

```yaml
部署方式: Kubernetes (EKS/GKE/AKS)

集群规模:
  节点类型: 
    - 通用节点: 2-10 个（自动扩展）
    - 数据库节点: 2 个（RDS/Cloud SQL）
  节点规格:
    CPU: 4-8 核
    内存: 16-32 GB

服务架构:
  Frontend:
    类型: Deployment
    副本数: 3-10（自动扩展）
    容器: node:20-alpine
    端口: 3000
    健康检查: HTTP /_health
  
  Backend:
    类型: Deployment
    副本数: 3-10（自动扩展）
    容器: python:3.11-slim
    端口: 8000
    健康检查: HTTP /health/
  
  Celery Worker:
    类型: Deployment
    副本数: 2-5
    队列: default, priority, low
  
  Celery Beat:
    类型: Deployment
    副本数: 1（单实例）
  
  PostgreSQL:
    类型: 托管服务 (RDS/Cloud SQL)
    规格: db.m6g.2xlarge (8 vCPU, 32 GB)
    存储: 500 GB SSD
    备份: 自动备份（保留 30 天）
    高可用: Multi-AZ
  
  Redis:
    类型: 托管服务 (ElastiCache/MemoryStore)
    规格: cache.m6g.large (2 vCPU, 6.38 GB)
    持久化: AOF
    高可用: 集群模式
  
  Nginx/ALB:
    类型: LoadBalancer
    SSL: ACM Certificate
    WAF: 启用

环境变量 (Backend):
  # Django
  DJANGO_ENV=production
  DEBUG=false
  SECRET_KEY=<ultra-secure-random-string>
  ALLOWED_HOSTS=posx.io,api.posx.io,www.posx.io
  
  # Database
  DATABASE_URL=postgresql://posx:xxx@posx-db.xxx.rds.amazonaws.com:5432/posx_prod
  
  # Redis
  REDIS_URL=redis://posx-redis.xxx.cache.amazonaws.com:6379/0
  
  # Auth0
  AUTH0_DOMAIN=posx.auth0.com
  AUTH0_AUDIENCE=https://api.posx.io
  AUTH0_ISSUER=https://posx.auth0.com/
  
  # Stripe (生产密钥)
  STRIPE_SECRET_KEY=sk_live_xxx
  STRIPE_PUBLISHABLE_KEY=pk_live_xxx
  STRIPE_WEBHOOK_SECRET=whsec_xxx
  
  # Fireblocks (生产环境)
  FIREBLOCKS_API_KEY=xxx
  FIREBLOCKS_PRIVATE_KEY=<encrypted-pem>
  FIREBLOCKS_BASE_URL=https://api.fireblocks.io
  FIREBLOCKS_VAULT_ACCOUNT_ID=0
  FIREBLOCKS_ASSET_ID=POSX
  FIREBLOCKS_WEBHOOK_PUBLIC_KEY=<pem-content>
  
  # Blockchain (主网)
  ETH_RPC_URL=https://mainnet.infura.io/v3/xxx
  TOKEN_CONTRACT_ADDRESS=0x...
  
  # Sentry
  SENTRY_DSN=https://xxx@sentry.io/xxx
  SENTRY_ENVIRONMENT=production
  SENTRY_TRACES_SAMPLE_RATE=0.1
  
  # AWS
  AWS_ACCESS_KEY_ID=xxx
  AWS_SECRET_ACCESS_KEY=xxx
  AWS_S3_BUCKET=posx-prod-assets
  AWS_REGION=us-east-1
  
  # 其他
  FRONTEND_URL=https://posx.io
  CORS_ALLOWED_ORIGINS=https://posx.io,https://www.posx.io
  ALLOWED_SITE_CODES=NA,ASIA
  LOG_LEVEL=WARNING

环境变量 (Frontend):
  # Auth0
  AUTH0_BASE_URL=https://posx.io
  AUTH0_ISSUER_BASE_URL=https://posx.auth0.com
  AUTH0_CLIENT_ID=xxx
  AUTH0_CLIENT_SECRET=xxx
  AUTH0_SECRET=<ultra-secure-random-string>
  
  # API
  NEXT_PUBLIC_API_URL=https://api.posx.io/api
  
  # Stripe
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_xxx
  
  # WalletConnect
  NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=xxx
  
  # Blockchain
  NEXT_PUBLIC_ETH_RPC_URL=https://mainnet.infura.io/v3/xxx
  NEXT_PUBLIC_TOKEN_CONTRACT_ADDRESS=0x...
  
  # Sentry
  NEXT_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/xxx
  NEXT_PUBLIC_SENTRY_ENVIRONMENT=production

域名配置:
  posx.io → Frontend (主域名)
  www.posx.io → Frontend (重定向)
  api.posx.io → Backend API
  admin.posx.io → Admin Backend
  
SSL 证书:
  提供商: AWS ACM / Let's Encrypt
  自动续期: 是
  HTTPS 强制: 是
  HSTS: 启用

CDN 配置:
  提供商: CloudFront / Cloudflare
  缓存策略:
    - 静态资源: 1 年
    - API 响应: 不缓存
    - HTML: 5 分钟
  
备份策略:
  数据库:
    - 自动备份: 每小时
    - 手动快照: 每周
    - 保留期: 30 天
    - 异地复制: 启用
  
  Redis:
    - AOF 持久化: 启用
    - 快照: 每日
    - 保留期: 7 天

监控指标:
  - CPU 使用率 > 80%
  - 内存使用率 > 85%
  - 磁盘使用率 > 80%
  - API 响应时间 > 1s
  - 错误率 > 1%
  - 数据库连接池耗尽
```

---

## 13. 部署规范

### 13.1 部署流程

```yaml
开发流程:
  1. 本地开发:
     - 创建功能分支
     - 编写代码 + 测试
     - 提交到 Git
  
  2. 代码审查:
     - 创建 Pull Request
     - 团队成员 Review
     - 修改并通过审查
  
  3. 合并主分支:
     - 合并到 main/develop
     - 自动触发 CI/CD
  
  4. 部署到 Demo:
     - 自动部署到 Demo 环境
     - 运行集成测试
     - UAT 验收测试
  
  5. 部署到生产:
     - 手动触发生产部署
     - 金丝雀发布（10% → 50% → 100%）
     - 监控指标
     - 出问题快速回滚

CI/CD 工具:
  推荐: GitHub Actions / GitLab CI / Jenkins
  
  Pipeline 阶段:
    - Lint: 代码检查
    - Test: 单元测试 + 集成测试
    - Build: 构建 Docker 镜像
    - Push: 推送到镜像仓库
    - Deploy: 部署到 K8s

部署策略:
  开发环境: 自动部署（每次 commit）
  Demo 环境: 自动部署（merge 到 develop）
  生产环境: 手动审批 + 金丝雀发布
```

### 13.2 Docker 镜像规范

```yaml
Backend Dockerfile:
  基础镜像: python:3.11-slim
  工作目录: /app
  
  构建阶段:
    1. 安装系统依赖
    2. 复制 requirements.txt
    3. 安装 Python 依赖
    4. 复制应用代码
    5. 收集静态文件
    6. 设置启动命令
  
  优化:
    - 使用多阶段构建
    - 缓存 Python 依赖层
    - 删除构建工具（减小体积）
    - 使用 .dockerignore
  
  安全:
    - 非 root 用户运行
    - 扫描漏洞
    - 定期更新基础镜像

Frontend Dockerfile:
  基础镜像: node:20-alpine
  工作目录: /app
  
  构建阶段:
    1. 复制 package.json
    2. 安装依赖
    3. 复制应用代码
    4. 构建生产版本
    5. 设置启动命令
  
  优化:
    - 使用多阶段构建
    - 缓存 node_modules 层
    - 使用 .dockerignore
    - 输出优化（next.config.js）

镜像标签规范:
  格式: {registry}/{repo}:{tag}
  
  标签策略:
    - latest: 最新版本
    - {version}: 语义化版本 (v1.0.0)
    - {branch}-{commit}: 分支 + Commit SHA
    - {env}: 环境标识 (demo/prod)

镜像仓库:
  开发/Demo: Docker Hub / GitHub Registry
  生产: ECR / GCR / ACR (私有仓库)
```

### 13.3 数据库迁移规范

```yaml
迁移工具: Django Migrations

迁移流程:
  1. 开发环境创建迁移:
     python manage.py makemigrations
  
  2. 本地测试:
     python manage.py migrate
     python manage.py migrate --fake-initial (如需)
  
  3. 提交到版本控制:
     git add migrations/
     git commit -m "Add xxx migration"
  
  4. 部署时自动执行:
     - Demo: 自动执行
     - 生产: 部署前手动执行（或自动 + 监控）

迁移检查:
  部署前:
    - MUST 在 Demo 环境测试
    - MUST 验证回滚脚本
    - SHOULD 评估执行时间
    - SHOULD 评估锁表影响
  
  部署时:
    - MUST 备份数据库
    - SHOULD 在维护窗口执行（大迁移）
    - MUST 监控执行状态
  
  部署后:
    - MUST 验证数据完整性
    - MUST 验证应用功能
    - SHOULD 性能回归测试

大迁移策略:
  - 分阶段执行（避免长时间锁表）
  - 先添加列（可空），后填充数据
  - 使用后台任务填充数据
  - 最后设置非空约束
```

---

## 14. 运维规范

### 14.1 日志规范

```yaml
日志级别:
  DEBUG: 调试信息（仅开发环境）
  INFO: 一般信息（业务操作）
  WARNING: 警告（可恢复错误）
  ERROR: 错误（需要关注）
  CRITICAL: 严重错误（需要立即处理）

日志内容:
  必含字段:
    - timestamp: ISO 8601 格式
    - level: 日志级别
    - logger: 日志来源
    - message: 日志消息
    - request_id: 请求唯一 ID
  
  可选字段:
    - user_id: 用户 ID
    - order_id: 订单 ID
    - error_code: 错误代码
    - stack_trace: 堆栈跟踪
    - extra: 额外信息

日志格式:
  开发环境: 控制台输出（彩色）
  生产环境: JSON 格式
  
  示例:
    {
      "timestamp": "2025-11-07T14:30:00.123Z",
      "level": "ERROR",
      "logger": "apps.orders.views",
      "message": "Order creation failed",
      "request_id": "uuid",
      "user_id": "uuid",
      "error_code": "ORDER_INSUFFICIENT_STOCK",
      "extra": {
        "tier_id": "uuid",
        "requested_quantity": 10,
        "available_quantity": 5
      }
    }

日志存储:
  开发环境: 本地文件
  Demo 环境: CloudWatch / 文件
  生产环境: CloudWatch / ELK Stack
  
  保留期限:
    - DEBUG: 1 天
    - INFO: 30 天
    - WARNING: 90 天
    - ERROR/CRITICAL: 1 年

日志安全:
  - MUST_NOT 记录密码
  - MUST_NOT 记录完整信用卡号
  - MUST_NOT 记录私钥
  - SHOULD 脱敏敏感信息
```

### 14.2 监控规范

```yaml
监控工具:
  应用监控: Sentry / New Relic
  基础设施监控: CloudWatch / Prometheus
  日志分析: ELK Stack / CloudWatch Logs
  实时监控: Grafana

监控指标:
  系统指标:
    - CPU 使用率
    - 内存使用率
    - 磁盘使用率
    - 网络流量
    - 磁盘 I/O
  
  应用指标:
    - 请求速率 (RPS)
    - 响应时间 (P50/P95/P99)
    - 错误率
    - 数据库连接池使用率
    - 缓存命中率
    - 队列长度
  
  业务指标:
    - 订单创建速率
    - 支付成功率
    - 代币发放速率
    - 注册用户数
    - 活跃用户数

健康检查:
  Backend:
    路径: /health/
    检查内容:
      - 数据库连接
      - Redis 连接
      - 磁盘空间
    响应格式:
      {
        "status": "healthy",
        "checks": {
          "database": "ok",
          "redis": "ok",
          "disk": "ok"
        },
        "timestamp": "2025-11-07T14:30:00Z"
      }
  
  Frontend:
    路径: /_health
    检查内容: 应用运行状态
    响应: 200 OK

告警触发:
  - 错误率 > 1%（5 分钟）
  - API 响应时间 P95 > 2s
  - CPU 使用率 > 80%（10 分钟）
  - 内存使用率 > 85%
  - 磁盘使用率 > 80%
  - 数据库连接池耗尽
  - Redis 连接失败
  - 支付失败率 > 5%
```

### 14.3 定时任务规范

```yaml
任务调度: Celery Beat

任务列表:
  1. 订单过期取消:
     周期: 每 5 分钟
     任务: cancel_expired_orders
     作用: 取消超时未支付订单
  
  2. 佣金冻结期释放:
     周期: 每小时
     任务: release_held_commissions
     作用: 解冻到期佣金
  
  3. 清理幂等键:
     周期: 每天 3:00
     任务: cleanup_idempotency_keys
     作用: 删除 48 小时前的幂等键
  
  4. 清理过期 Nonce:
     周期: 每小时
     任务: cleanup_expired_nonces
     作用: 删除过期 Nonce
  
  5. 同步 Fireblocks 余额:
     周期: 每 10 分钟
     任务: sync_fireblocks_balances
     作用: 同步用户代币余额
  
  6. 数据库备份验证:
     周期: 每天 2:00
     任务: verify_database_backup
     作用: 验证备份可用性
  
  7. 生成日报:
     周期: 每天 8:00
     任务: generate_daily_report
     作用: 生成运营日报

任务配置:
  重试策略:
    - 最大重试次数: 3
    - 重试延迟: 指数退避 (60s, 120s, 240s)
    - 失败告警: Sentry
  
  超时配置:
    - 软超时: 300 秒
    - 硬超时: 600 秒
  
  并发控制:
    - 队列隔离（default/priority/low）
    - 限流（避免压垮数据库）

监控告警:
  - 任务执行失败
  - 任务执行超时
  - 任务队列堆积
  - Celery Worker 宕机
```

---

## 15. 监控与告警规范

### 15.1 告警规则

```yaml
告警级别:
  P0 - Critical:
    影响: 核心功能不可用
    响应时间: 15 分钟
    通知方式: 电话 + 短信 + Slack
    示例:
      - 数据库宕机
      - 所有 API 不可用
      - 支付系统故障
  
  P1 - High:
    影响: 重要功能受影响
    响应时间: 1 小时
    通知方式: Slack + Email
    示例:
      - 错误率 > 5%
      - API 响应时间 > 5s
      - Celery Worker 全部宕机
  
  P2 - Medium:
    影响: 部分功能受影响
    响应时间: 4 小时
    通知方式: Slack
    示例:
      - 错误率 > 1%
      - CPU 使用率 > 80%
      - 队列堆积
  
  P3 - Low:
    影响: 可忽略
    响应时间: 1 个工作日
    通知方式: Email
    示例:
      - 磁盘使用率 > 70%
      - 缓存命中率 < 80%

告警规则:
  数据库:
    - 连接数 > 80% (P2)
    - 慢查询 > 100/min (P2)
    - 复制延迟 > 60s (P1)
    - 磁盘使用率 > 80% (P2)
  
  API:
    - 错误率 > 1% (P2)
    - 错误率 > 5% (P1)
    - 响应时间 P95 > 2s (P2)
    - 响应时间 P95 > 5s (P1)
    - 所有请求失败 (P0)
  
  支付:
    - Stripe Webhook 失败率 > 5% (P1)
    - 支付成功率 < 95% (P1)
    - 争议创建 (P2)
  
  代币分配:
    - Fireblocks Webhook 失败率 > 5% (P1)
    - 发放失败率 > 10% (P2)
  
  队列:
    - 队列长度 > 1000 (P2)
    - 队列长度 > 10000 (P1)
    - Worker 全部宕机 (P1)

告警抑制:
  - 维护窗口期间静音
  - 已知问题标记（避免重复告警）
  - 告警聚合（5 分钟内相同告警合并）
```

### 15.2 事件响应

```yaml
响应流程:
  1. 接收告警:
     - 通过 Slack / PagerDuty 接收
     - 确认告警（ACK）
  
  2. 初步诊断:
     - 查看监控面板
     - 查看日志
     - 确定影响范围
  
  3. 应急处理:
     - P0: 立即回滚或切换备用
     - P1: 尝试修复或降级
     - P2: 计划修复
  
  4. 根因分析:
     - 查找根本原因
     - 编写事故报告
  
  5. 改进措施:
     - 修复 Bug
     - 改进监控
     - 更新 Runbook

常见问题 Runbook:
  数据库连接池耗尽:
    诊断:
      - 检查连接数: SELECT count(*) FROM pg_stat_activity
      - 检查长事务: SELECT * FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '5 minutes'
    处理:
      - 杀死长事务
      - 重启应用（释放连接）
      - 增加连接池大小（如需）
  
  订单超卖:
    诊断:
      - 检查 tier.sold_units > tier.total_units
      - 检查并发订单日志
    处理:
      - 回滚超卖订单
      - 退款给用户
      - 修复并发控制 Bug
  
  Webhook 处理失败:
    诊断:
      - 检查 webhook_logs 表
      - 检查 Celery 队列
      - 检查错误日志
    处理:
      - 重试失败的 Webhook
      - 修复处理逻辑
      - 联系第三方（如持续失败）
```

---

## 16. 术语表

```yaml
核心术语:
  Site: 站点，独立运营的区域（如 NA, ASIA）
  Tier: 档位，不同价格和代币数量的购买选项
  Order: 订单，用户购买代币的记录
  Allocation: 分配，代币发放记录
  Commission: 佣金，推荐奖励
  Wallet: 钱包，用户接收代币的地址
  Nonce: 一次性随机数，用于防重放攻击

状态术语:
  Pending: 待处理
  Processing: 处理中
  Completed: 已完成
  Failed: 失败
  Cancelled: 已取消
  Hold: 冻结
  Ready: 就绪
  Paid: 已支付
  Disputed: 有争议

技术术语:
  Idempotency: 幂等性，相同请求产生相同结果
  Optimistic Lock: 乐观锁，通过版本号控制并发
  Webhook: Web 回调，第三方服务事件通知
  JWT: JSON Web Token，身份认证令牌
  RSA: 非对称加密算法
  HMAC: 基于哈希的消息认证码
  SIWE: Sign-In with Ethereum，以太坊钱包登录
  RBAC: 基于角色的访问控制

第三方服务:
  Auth0: 身份认证服务
  Stripe: 支付处理服务
  Fireblocks: 数字资产托管服务
  WalletConnect: Web3 钱包连接协议
  Sentry: 错误监控服务

缩写:
  API: Application Programming Interface
  REST: Representational State Transfer
  JWT: JSON Web Token
  UUID: Universally Unique Identifier
  CSRF: Cross-Site Request Forgery
  XSS: Cross-Site Scripting
  SQL: Structured Query Language
  ORM: Object-Relational Mapping
  CI/CD: Continuous Integration/Continuous Deployment
  K8s: Kubernetes
  RPS: Requests Per Second
  P50/P95/P99: 百分位数（中位数/95分位/99分位）
```

---

## 附录 A: 上线前检查清单

```yaml
数据库检查:
  [ ] 所有迁移脚本已执行
  [ ] 所有索引已创建
  [ ] 所有约束已创建
  [ ] 所有触发器已创建
  [ ] 数据库备份已配置
  [ ] 备份恢复已测试

环境变量检查:
  [ ] 所有环境变量已配置
  [ ] 生产密钥已替换（不是测试密钥）
  [ ] 敏感信息已加密
  [ ] Auth0 配置正确
  [ ] Stripe 生产密钥配置
  [ ] Fireblocks 生产配置

第三方集成检查:
  [ ] Auth0 应用配置完成
  [ ] Stripe Webhook 已订阅
  [ ] Fireblocks Webhook 已配置
  [ ] WalletConnect Project 已创建
  [ ] Sentry 项目已创建

功能测试:
  [ ] 用户注册登录（3 种方式）
  [ ] 钱包绑定/解绑
  [ ] 档位浏览
  [ ] 订单创建
  [ ] Stripe 支付
  [ ] Webhook 处理
  [ ] 代币余额查询
  [ ] 佣金生成
  [ ] 管理后台功能

性能测试:
  [ ] 并发订单测试（1000+ 并发）
  [ ] 库存控制测试
  [ ] API 响应时间测试
  [ ] 数据库查询性能
  [ ] 缓存命中率测试

安全测试:
  [ ] SQL 注入测试
  [ ] XSS 攻击测试
  [ ] CSRF 攻击测试
  [ ] JWT 验证测试
  [ ] 权限控制测试
  [ ] 限流测试
  [ ] Webhook 签名验证

监控告警:
  [ ] Sentry 集成测试
  [ ] CloudWatch 告警配置
  [ ] Slack 告警通知测试
  [ ] 健康检查配置
  [ ] 日志收集配置

部署准备:
  [ ] Docker 镜像已构建
  [ ] K8s 配置已准备
  [ ] 域名 DNS 已配置
  [ ] SSL 证书已配置
  [ ] CDN 已配置
  [ ] 负载均衡已配置

运维准备:
  [ ] Runbook 已编写
  [ ] 团队培训已完成
  [ ] 回滚计划已准备
  [ ] 客服团队已培训
  [ ] 监控面板已配置
```

---

## 附录 B: 版本规范

```yaml
版本号格式: MAJOR.MINOR.PATCH

递增规则:
  MAJOR: 不兼容的 API 变更
  MINOR: 向下兼容的功能新增
  PATCH: 向下兼容的 Bug 修复

示例:
  v1.0.0: 初始版本
  v1.0.1: Bug 修复
  v1.1.0: 新增功能
  v2.0.0: 破坏性变更

Git Tag:
  格式: v{version}
  示例: v1.0.0, v1.1.0

Release Notes:
  必含内容:
    - 版本号
    - 发布日期
    - 新增功能
    - Bug 修复
    - 破坏性变更
    - 升级指南
```

---

## 文档维护

```yaml
更新频率:
  - 重大变更: 立即更新
  - 功能新增: 每次发版更新
  - Bug 修复: 季度汇总

审核流程:
  - 技术负责人审核
  - 架构师审核
  - 文档归档

版本控制:
  - 所有变更记录在版本历史
  - 重大变更需要说明理由
  - 保留历史版本（至少 3 个）
```

---

**文档结束**

**版本：** v1.0.0  
**发布日期：** 2025-11-07  
**下次审查日期：** 2025-12-07  
**维护者：** System Architect Team

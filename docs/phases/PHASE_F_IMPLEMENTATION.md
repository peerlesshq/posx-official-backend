# Phase F 实施文档

**阶段**: F - Agent 佣金深化、CRM 与报表  
**版本**: v1.1  
**状态**: ✅ 已完成核心功能  

---

## 📋 实施概述

Phase F 在 Phase A-E 的基础上，深化了 Agent 佣金系统，新增：
- 内部余额账户与提现流程
- 多层级佣金配置（2-10级）
- Agent Dashboard（基础 CRM）
- 双向报表系统（管理员监控 + Agent 自查）

---

## 🎯 核心特性

### 1. 内部余额账户（AgentProfile）

**模型**: `apps/agents/models.py::AgentProfile`

**字段**:
- `balance_usd`: 可提现余额
- `total_earned_usd`: 累计收入
- `total_withdrawn_usd`: 累计提现
- `agent_level`: 代理等级（bronze/silver/gold/platinum）
- `kyc_status`: KYC 认证状态

**约束**:
- `balance_usd >= 0`（CheckConstraint）
- `(site, user)` 唯一（UniqueConstraint）

### 2. 提现申请流程（WithdrawalRequest）

**模型**: `apps/agents/models.py::WithdrawalRequest`

**状态机**:
```
submitted（提交，扣减余额）
   ↓
approved（审核通过）
   ↓
completed（转账完成，记录 total_withdrawn）

   ↓（分支）
rejected/cancelled（拒绝/取消，返还余额）
```

**API 端点**:
- `POST /api/v1/agents/withdrawal/` - 提交申请
- `GET /api/v1/agents/withdrawal-requests/` - 查询记录

**Admin Action**:
- 批准选中的申请
- 拒绝选中的申请（返还余额）
- 标记完成（已转账）

### 3. 多层级佣金方案（CommissionPlan）

**模型**: `apps/commissions/models.py::CommissionPlan` + `CommissionPlanTier`

**设计**:
```
CommissionPlan（方案）
├─ name: "标准方案"
├─ max_levels: 2
├─ is_default: true
└─ tiers:
    ├─ L1: 12%, hold 7天
    └─ L2: 4%, hold 7天

CommissionPlan（高级方案）
├─ name: "高级方案"
├─ max_levels: 3
├─ is_default: false
└─ tiers:
    ├─ L1: 15%, hold 7天
    ├─ L2: 5%, hold 7天
    └─ L3: 2%, hold 7天
```

**API 端点**:
- `GET /api/v1/commissions/plans/` - 列表
- `POST /api/v1/commissions/plans/` - 创建（仅管理员）
- `PUT /api/v1/commissions/plans/{id}/` - 更新（仅管理员）
- `POST /api/v1/commissions/plans/{id}/set-default/` - 设为默认

### 4. Agent Dashboard

**API 端点**: `GET /api/v1/agents/dashboard/`

**响应结构**:
```json
{
  "balance": {
    "available": "1234.56",
    "pending_commissions": {
      "hold": "100.00",
      "ready": "200.00"
    }
  },
  "performance": {
    "total_sales": "10000.00",
    "total_orders": 50,
    "this_month_sales": "2000.00",
    "this_month_orders": 10
  },
  "team": {
    "total_downlines": 50,
    "max_depth": 5
  },
  "recent_commissions": [...],
  "recent_orders": [...]
}
```

### 5. 管理员报表系统

**API 端点**（需超级管理员权限）:

- `GET /api/admin-api/reports/overview/` - 全站业绩概览
  - 参数：site_code, date_from, date_to
  - 返回：销售额、订单数、佣金统计、Top 10 Agents

- `GET /api/admin-api/reports/leaderboard/` - Agent 排行榜
  - 参数：period, metric, limit
  - 返回：按销售额/佣金排序的 Agent 列表

- `GET /api/admin-api/reports/reconciliation/` - 佣金对账报表
  - 参数：period, site_code
  - 返回：按状态/层级统计的佣金数据

- `GET /api/admin-api/reports/anomalies/` - 异常监控
  - 返回：卡住的佣金、失败分配、争议订单、不活跃 Agent

### 6. 月度对账单（CommissionStatement）

**生成方式**: Celery 定时任务（每月 1 号凌晨 2 点）

**内容**:
- 本期佣金总额
- 已结算/未结算金额
- 订单数、客户数
- PDF 导出（TODO）

**API 端点**: `GET /api/v1/agents/statements/`

---

## 📁 新增文件清单（Phase F）

### 模型与迁移
- `backend/apps/agents/models.py` - 扩展（+3个模型）
- `backend/apps/agents/migrations/0002_agent_extensions.py` - 新迁移
- `backend/apps/commissions/models.py` - 扩展（+2个模型）
- `backend/apps/commissions/migrations/0002_commission_plans.py` - 新迁移

### 服务层
- `backend/apps/agents/services/balance.py` - 余额管理服务
- `backend/apps/agents/tasks.py` - Celery 任务

### API 层
- `backend/apps/agents/serializers.py` - 扩展（+4个序列化器）
- `backend/apps/agents/views.py` - 扩展（+4个 action）
- `backend/apps/agents/admin.py` - Admin 管理界面
- `backend/apps/commissions/serializers_plans.py` - Plan 序列化器
- `backend/apps/commissions/views_plans.py` - Plan ViewSet
- `backend/apps/admin/views.py` - 管理员报表视图

### 配置
- `backend/config/celery.py` - 更新（+2个定时任务）
- `backend/config/urls.py` - 更新（+admin-api路由）
- `backend/apps/commissions/urls.py` - 更新（+plans路由）
- `backend/apps/admin/urls.py` - 更新（+报表路由）

---

## 🧪 验收命令

### 1. 应用迁移

```bash
# 查看待应用迁移
docker-compose exec backend python manage.py showmigrations agents commissions

# 应用迁移
docker-compose exec backend python manage.py migrate

# 预期输出:
# Applying agents.0002_agent_extensions... OK
# Applying commissions.0002_commission_plans... OK
```

### 2. 验证表结构

```bash
# 检查 agent_profiles 表
docker-compose exec postgres psql -U posx_app -d posx_local -c "\d agent_profiles"

# 预期包含:
# - balance_usd (numeric(18,6))
# - Constraint: chk_agent_profile_balance_non_negative

# 检查 commission_plans 表
docker-compose exec postgres psql -U posx_app -d posx_local -c "\d commission_plans"

# 预期包含:
# - max_levels (smallint)
# - is_default (boolean)
```

### 3. 测试 API 端点

```bash
# 获取 JWT Token
export TOKEN="Bearer eyJ..."

# 1. 查询余额
curl -H "Authorization: $TOKEN" \
     -H "X-Site-Code: NA" \
     http://localhost:8000/api/v1/agents/me/balance/

# 预期:
# {
#   "balance_usd": "0.00",
#   "total_earned_usd": "0.00",
#   "total_withdrawn_usd": "0.00",
#   "pending_commissions": {
#     "hold": "0.00",
#     "ready": "0.00"
#   }
# }

# 2. 查询 Dashboard
curl -H "Authorization: $TOKEN" \
     -H "X-Site-Code: NA" \
     http://localhost:8000/api/v1/agents/dashboard/

# 预期:
# {
#   "balance": {...},
#   "performance": {...},
#   "team": {...},
#   "recent_commissions": [],
#   "recent_orders": []
# }

# 3. 提交提现申请
curl -X POST http://localhost:8000/api/v1/agents/withdrawal/ \
  -H "Authorization: $TOKEN" \
  -H "X-Site-Code: NA" \
  -H "Content-Type: application/json" \
  -d '{
    "amount_usd": "100.00",
    "withdrawal_method": "bank_transfer",
    "account_info": {
      "bank_name": "Test Bank",
      "account_number": "123456789",
      "account_holder": "John Doe"
    }
  }'

# 预期（余额不足时）:
# 400 Bad Request
# {
#   "code": "WITHDRAWAL.INSUFFICIENT_BALANCE",
#   "message": "余额不足。可用余额：$0.00"
# }

# 4. 管理员查询报表（需超级管理员）
curl -H "Authorization: $ADMIN_TOKEN" \
     http://localhost:8000/api/admin-api/reports/overview/?site_code=NA

# 预期:
# {
#   "period": {"from": "...", "to": "..."},
#   "total_sales": "0.00",
#   "total_orders": 0,
#   "top_agents": []
# }
```

### 4. 测试 Celery 任务

```bash
# 1. 手动触发对账单生成
docker-compose exec backend python manage.py shell
>>> from apps.agents.tasks import generate_monthly_statements
>>> result = generate_monthly_statements()
>>> print(result)
{'generated': 0, 'skipped': 0, 'period': '...'}

# 2. 手动触发统计更新
>>> from apps.agents.tasks import update_agent_stats
>>> result = update_agent_stats()
>>> print(result)
{'updated': 0}
```

### 5. 测试 Admin 界面

```
访问: http://localhost:8000/admin/

新增模块:
- Agent Profiles
- Withdrawal Requests
- Commission Statements
- Agent Trees
- Agent Stats

测试流程:
1. 创建 AgentProfile（手动或自动创建）
2. 模拟余额（手动更新 balance_usd）
3. 创建 WithdrawalRequest
4. 使用 Admin Action 批准/拒绝/完成
```

---

## 🔐 环境变量配置

新增配置（添加到 `.env`）:

```bash
# Phase F: 提现配置
WITHDRAWAL_MIN_AMOUNT=50.00  # 最小提现金额
WITHDRAWAL_FEE_PERCENT=0.00  # 提现手续费比例（暂不收取）
WITHDRAWAL_ADMIN_EMAILS=admin@posx.io  # 提现通知邮箱（逗号分隔）
```

---

## 📊 数据流程

### 余额更新流程

```
Phase D: Commission 结算
  → status: ready → paid
  → 触发 update_balance_on_commission_paid()
  → AgentProfile.balance_usd += commission_amount
  → AgentProfile.total_earned_usd += commission_amount
```

### 提现流程

```
1. Agent 提交申请
   → POST /agents/withdrawal/
   → 验证余额
   → 扣减 balance_usd（悲观锁）
   → 创建 WithdrawalRequest(status='submitted')

2. Admin 审核
   → Admin 界面批量操作
   → approved: status = 'approved'
   → rejected: status = 'rejected', 返还余额

3. Admin 确认转账
   → complete action
   → status = 'completed'
   → AgentProfile.total_withdrawn_usd += amount
```

### 对账单生成流程

```
Celery 定时任务（每月1号凌晨2点）
  → 查询上月所有活跃 Agent
  → 统计佣金数据（total/paid/pending）
  → 统计订单数据（order_count/customer_count）
  → 创建 CommissionStatement 记录
  → 发送邮件通知（TODO）
```

---

## 🚨 安全注意事项

### 1. 余额并发安全

使用悲观锁（select_for_update）:

```python
with transaction.atomic():
    profile = AgentProfile.objects.select_for_update().get(
        profile_id=profile_id
    )
    profile.balance_usd += amount
    profile.save()
```

### 2. 管理员报表使用 Admin 连接

```python
with connections['admin'].cursor() as cursor:
    cursor.execute("SELECT ...")  # 绕过 RLS
```

### 3. 敏感信息加密

`WithdrawalRequest.account_info`（JSONField）:
- 存储前加密（TODO: 应用层加密）
- API 返回时不包含（write_only）
- Admin 界面可见但受权限保护

---

## 📈 性能优化

### 1. AgentStats 预计算

- 每小时更新一次
- Dashboard 优先使用预计算数据
- 减少实时聚合查询

### 2. 对账单缓存

- 对账单一旦生成不再变化
- 可缓存 PDF 文件（未来）

### 3. 报表查询优化

- 使用 Admin 连接（无 RLS 开销）
- 索引优化（site_id, created_at, status）
- 分页（leaderboard 限制≤100）

---

## 🔄 与其他 Phase 的集成

### 与 Phase D 集成

```python
# Phase D: Commission Admin 批量结算
def settle_commissions(self, request, queryset):
    # ... 原有逻辑 ...
    
    # ⭐ Phase F: 更新余额
    for commission in ready_commissions:
        update_balance_on_commission_paid(commission)
```

### 与 Phase E 集成

无直接集成，独立运行。

---

## 📊 成功指标

### 功能指标
- AgentProfile 余额正确同步：100%
- 提现申请流程完整：100%
- 对账单自动生成：100%
- Dashboard API 可用：100%
- 管理员报表准确：100%

### 性能指标
- Dashboard API < 500ms
- 报表查询 < 2s
- 余额更新 < 100ms（悲观锁）
- 对账单生成 < 30s/Agent

---

## ✅ 验收清单

- [x] AgentProfile 模型与迁移
- [x] WithdrawalRequest 模型与迁移
- [x] CommissionStatement 模型与迁移
- [x] CommissionPlan 模型与迁移
- [x] CommissionPlanTier 模型与迁移
- [x] 余额管理服务（balance.py）
- [x] 提现申请 API
- [x] Agent Dashboard API
- [x] 管理员报表 API（4个端点）
- [x] 提现审核 Admin 界面
- [x] 对账单生成 Celery 任务
- [x] Agent 统计更新 Celery 任务
- [x] Celery Beat 配置更新
- [ ] 单元测试（TODO）
- [ ] PDF 生成服务（TODO）
- [ ] 邮件通知（TODO）

---

## 📝 TODO（后续优化）

### 高优先级
1. **PDF 对账单生成**（weasyprint）
2. **邮件通知**（提现申请、审核结果）
3. **单元测试**（覆盖率 >85%）

### 中优先级
4. **account_info 加密**（cryptography）
5. **Agent 等级自动升级**（基于业绩）
6. **推荐链接生成 API**（带二维码）

### 低优先级
7. **Dashboard 前端页面**（Next.js）
8. **报表图表可视化**（Chart.js）
9. **批量导出功能**（CSV/Excel）

---

**Phase F 核心功能已完成，可立即使用！** 🚀


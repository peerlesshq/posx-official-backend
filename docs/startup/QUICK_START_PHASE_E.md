# 🚀 Phase E 快速启动指南

**版本**: v2.2.1  
**更新**: 2025-11-09

---

## 📋 前置准备

### 1. 安装依赖

```powershell
cd E:\300_Code\314_POSX_Official_Sale_App\backend

# 激活虚拟环境
.\venv\Scripts\activate

# 安装新依赖
pip install web3 base58 PyJWT cryptography prometheus-client
```

### 2. 配置环境变量

在 `.env` 文件中添加：

```bash
# Phase E: Vesting 配置
FIREBLOCKS_MODE=MOCK
ALLOW_PROD_TX=0
MOCK_TX_COMPLETE_DELAY=3
MOCK_WEBHOOK_URL=http://localhost:8000/api/v1/webhooks/fireblocks/

# LIVE 配置（暂时留空）
FIREBLOCKS_API_KEY=
FIREBLOCKS_PRIVATE_KEY=
FIREBLOCKS_BASE_URL=https://api.fireblocks.io
FIREBLOCKS_VAULT_ACCOUNT_ID=0
FIREBLOCKS_ASSET_ID=POSX_ETH
FIREBLOCKS_WEBHOOK_PUBLIC_KEY=
FIREBLOCKS_WEBHOOK_PUBLIC_KEY_2=
```

### 3. 运行数据库迁移

```powershell
# 生成迁移文件
python manage.py makemigrations

# 查看迁移SQL（可选）
python manage.py sqlmigrate sites 0002
python manage.py sqlmigrate webhooks 0002
python manage.py sqlmigrate vesting 0001

# 执行迁移
python manage.py migrate
```

**预期迁移**:
- `sites` - 添加 `chain_asset_configs` 表
- `webhooks` - 更新 `idempotency_keys` 唯一约束
- `vesting` - 创建 `vesting_policies/schedules/releases` 表
- `allocations` - 添加 `released_tokens` 字段

---

## 🎯 功能测试

### 测试 1: 创建测试数据

```python
# python manage.py shell

from decimal import Decimal
from django.utils import timezone
from apps.sites.models import Site, ChainAssetConfig
from apps.users.models import User
from apps.tiers.models import Tier
from apps.orders.models import Order
from apps.allocations.models import Allocation
from apps.vesting.models import VestingPolicy, VestingSchedule, VestingRelease
from apps.vesting.services.vesting_service import create_vesting_schedule

# 1. 获取或创建站点
site = Site.objects.first()

# 2. 创建资产配置
asset_config, _ = ChainAssetConfig.objects.get_or_create(
    site=site,
    chain='ETH',
    token_symbol='POSX',
    defaults={
        'token_decimals': 18,
        'fireblocks_asset_id': 'POSX_ETH',
        'address_type': 'EVM',
        'is_active': True
    }
)

# 3. 创建释放策略
policy, _ = VestingPolicy.objects.get_or_create(
    site=site,
    name='10% TGE + 12 Months',
    defaults={
        'tge_percent': Decimal('10.00'),
        'cliff_months': 0,
        'linear_periods': 12,
        'period_unit': 'month',
        'is_active': True
    }
)

# 4. 创建测试用户
user, _ = User.objects.get_or_create(
    wallet_address='0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
    defaults={'site': site}
)

# 5. 创建测试订单（假设已支付）
order = Order.objects.create(
    site=site,
    buyer=user,
    tier=Tier.objects.first(),  # 假设有 tier
    status='paid',
    final_price_usd=Decimal('1000.00'),
    wallet_address=user.wallet_address,
    paid_at=timezone.now()
)

# 6. 创建 allocation
allocation = Allocation.objects.create(
    order=order,
    wallet_address=user.wallet_address,
    token_amount=Decimal('10000.000000'),
    status='active',
    released_tokens=Decimal('0')
)

# 7. 创建 vesting schedule（会自动生成 releases）
schedule = create_vesting_schedule(
    site=site,
    order=order,
    user=user,
    allocation=allocation,
    policy=policy,
    total_tokens=Decimal('10000.000000')
)

print(f"✅ Schedule created: {schedule.schedule_id}")
print(f"   TGE: {schedule.tge_tokens}")
print(f"   Locked: {schedule.locked_tokens}")

# 8. 查看生成的 releases
releases = VestingRelease.objects.filter(schedule=schedule).order_by('period_no')
for r in releases:
    print(f"   P{r.period_no}: {r.amount} ({r.status}) - {r.release_date}")

# 验证总和
total = sum(r.amount for r in releases)
print(f"   Total: {total} (expected: {schedule.total_tokens})")
print(f"   Match: {total == schedule.total_tokens}")
```

### 测试 2: Admin 批量发放

1. 访问 Admin:
```
http://localhost:8000/admin/vesting/vestingrelease/
```

2. **验证显示**:
   - ✅ 顶部显示 🧪 MOCK 徽标
   - ✅ 看到 Period 0 (TGE) 状态为 `unlocked` (绿色)
   - ✅ 其他期数状态为 `locked` (灰色)

3. **执行批量发放**:
   - 勾选 Period 0 (TGE)
   - Action 选择：**📤 批量发放代币**
   - 点击执行

4. **预期结果**:
```
🧪 MOCK模式（不会上链）
批量发放完成：
✅ 提交: 1 条
❌ 失败: 0 条
⏭️ 跳过: 0 条
💰 总金额: 1,000.000000 tokens
```

5. **刷新页面**:
   - Period 0 状态变为 `processing` (黄色)
   - 显示 `tx_mock_*` 交易ID

6. **等待 3 秒后再刷新**:
   - Period 0 状态变为 `released` (蓝色)
   - 显示 `0xmock*` 交易哈希

### 测试 3: 验证 Allocation 累加

```python
# python manage.py shell

from apps.allocations.models import Allocation

allocation = Allocation.objects.first()
print(f"Token amount: {allocation.token_amount}")
print(f"Released tokens: {allocation.released_tokens}")
print(f"Status: {allocation.status}")

# 预期：
# Token amount: 10000.000000
# Released tokens: 1000.000000  # TGE 已发放
# Status: active  # 仍有未发放
```

### 测试 4: Admin 限流

1. 在 Admin 中连续点击批量发放 7 次
2. 第 7 次应该提示：
```
⚠️ 操作过于频繁，请稍后再试（限制：6次/分钟）
```

### 测试 5: Prometheus 指标

```bash
# 访问指标端点（需先添加 /metrics 路由）
curl http://localhost:8000/metrics | grep vesting

# 预期输出（示例）:
# vesting_batch_submitted_total{mode="MOCK",site_id="xxx"} 1.0
# vesting_webhook_completed_total{status="COMPLETED"} 1.0
# vesting_processing_stuck_gauge 0.0
```

---

## 🔧 启动服务

### 终端 1: Django

```powershell
cd backend
python manage.py runserver
```

### 终端 2: Celery Worker

```powershell
cd backend
celery -A config worker -l info
```

### 终端 3: Celery Beat

```powershell
cd backend
celery -A config beat -l info
```

**验证 Beat 任务已注册**:
```
[tasks]
  . apps.vesting.tasks.unlock_vesting_releases
  . apps.vesting.tasks.reconcile_stuck_releases
  . apps.vesting.tasks.cleanup_old_idempotency_keys
```

---

## ✅ 验收检查

### 数据库层

- [ ] 迁移成功执行（`python manage.py showmigrations`）
- [ ] `chain_asset_configs` 表已创建
- [ ] `vesting_policies/schedules/releases` 表已创建
- [ ] `allocations.released_tokens` 字段已添加
- [ ] `idempotency_keys` 有 `unique_together` 约束

### 功能层

- [ ] 可以创建 VestingSchedule
- [ ] Releases 自动生成（TGE + N 期）
- [ ] 总和验证通过（无尾差）
- [ ] Admin 批量发放可用
- [ ] MOCK webhook 3秒后触发
- [ ] Allocation.released_tokens 正确累加

### 安全层

- [ ] Admin 限流生效（7次/分钟被拦截）
- [ ] MOCK webhook 仅接受本地 IP
- [ ] 幂等性防重复（重复调用返回 duplicate）

### 指标层

- [ ] Prometheus 指标可访问
- [ ] 批量发放指标递增
- [ ] Webhook 指标递增
- [ ] 堆积指标正确更新

---

## 🆘 常见问题

### Q1: 迁移失败 - ChainAssetConfig 已存在？

**A**: 可能已有旧迁移，删除并重新生成：
```bash
# 查看迁移状态
python manage.py showmigrations sites

# 如果有冲突，回滚
python manage.py migrate sites zero
python manage.py migrate sites
```

### Q2: Celery 任务未执行？

**A**: 检查 Worker 是否运行：
```bash
# 查看活跃任务
celery -A config inspect active

# 查看注册任务
celery -A config inspect registered | grep vesting
```

### Q3: MOCK webhook 未收到？

**A**: 检查以下几点：
1. Celery Worker 运行中
2. Django 运行在 8000 端口
3. 查看 Celery 日志：`[MOCK Webhook] Sent successfully`
4. 查看 Django 日志：`[Fireblocks] Webhook received`

### Q4: 总和验证失败？

**A**: 这是 v2.2.1 的新保护机制：
```python
# 检查 locked_tokens 和 linear_periods 配置
# 确保可以整除或尾差在合理范围内
```

---

## 📊 监控指标说明

### 关键指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| `vesting_processing_stuck_gauge` | Processing 超过15分钟的数量 | > 10 |
| `vesting_unlocked_pending_gauge` | 待发放的 unlocked 数量 | > 1000 |
| `vesting_batch_failed_total` | 批量发放失败次数 | 失败率 > 10% |
| `vesting_webhook_duplicate_total` | 重复 webhook 数量 | - |

### Grafana 查询示例

```promql
# Processing 堆积趋势
vesting_processing_stuck_gauge

# 批量发放成功率（5分钟）
sum(rate(vesting_batch_submitted_total[5m])) / 
(sum(rate(vesting_batch_submitted_total[5m])) + sum(rate(vesting_batch_failed_total[5m])))

# Webhook 完成率
sum(rate(vesting_webhook_completed_total{status="COMPLETED"}[5m]))
```

---

## 📚 相关文档

- **v2.2.1 微调总结**: `docs/phases/PHASE_E_v2.2.1_SUMMARY.md`
- **环境变量配置**: `docs/config/CONFIG_PHASE_E_ENV.md`
- **Nginx 配置**: `docs/deployment/NGINX_FIREBLOCKS_WEBHOOK.md`
- **文件快速参考**: `docs/phases/PHASE_E_FILES_QUICK_REFERENCE.md`

---

**准备就绪，开始测试！** 🎉


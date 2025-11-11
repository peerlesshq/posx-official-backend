# Commission Plans 系统统一迁移指南

**版本**: v1.1.0  
**日期**: 2025-11-10  
**状态**: ⚠️ commission_plans app 已废弃

---

## 背景

POSX 系统目前存在两套佣金配置系统：

1. **commission_plans app** (已废弃)
   - 位置：`backend/apps/commission_plans/`
   - 特点：版本化管理，支持 effective_from/to
   - 状态：⚠️ 已标记为废弃

2. **commissions.CommissionPlan** (推荐使用)
   - 位置：`backend/apps/commissions/models.py`
   - 特点：简化设计，默认方案设置，完整功能
   - 状态：✅ 活跃开发，推荐使用

---

## 为什么统一？

### 问题

1. **功能重复**：两个系统提供相似功能
2. **维护成本高**：需要同时维护两套代码
3. **混淆风险**：开发者不确定使用哪个
4. **数据分散**：佣金配置分散在两个 app

### 解决方案

统一使用 `apps.commissions.CommissionPlan`，因为：
- ✅ 已集成到佣金计算逻辑（tasks.py）
- ✅ 支持默认方案设置
- ✅ API 完整且稳定
- ✅ 测试覆盖完整

---

## 功能对比

| 功能 | commission_plans | commissions.CommissionPlan |
|------|------------------|----------------------------|
| 多层级配置（1-10级） | ✅ | ✅ |
| 版本化管理 | ✅ | ✅（通过 plan_id） |
| 时间范围控制 | ✅ (effective_from/to) | ⚠️ 未实现 |
| 默认方案设置 | ❌ | ✅ (is_default) |
| 计算模式支持 | ✅ (mode 字段) | ✅ (实际未使用) |
| API 完整度 | ⚠️ 部分实现 | ✅ 完整 |
| 与计算逻辑集成 | ❌ | ✅ |
| 销售额门槛 | ✅ (min_sales) | ✅ (min_order_amount) |
| 差额封顶 | ✅ (diff_cap_percent) | ❌ |

**推荐**: 使用 `commissions.CommissionPlan`，如需时间范围功能可后续补充。

---

## 迁移步骤

### Phase 1: 新项目（立即生效）

**直接使用推荐系统**：
```python
from apps.commissions.models import CommissionPlan, CommissionPlanTier

# 创建佣金方案
plan = CommissionPlan.objects.create(
    site=site,
    name='标准方案',
    max_levels=2,
    is_default=True,
    is_active=True
)

# 创建层级配置
CommissionPlanTier.objects.create(
    plan=plan,
    level=1,
    rate_percent=Decimal('12.00'),
    hold_days=7,
    min_order_amount=Decimal('0')
)
```

### Phase 2: 现有项目（渐进式迁移）

#### Step 1: 数据迁移脚本

创建 Django migration 或手动脚本：

```python
# backend/scripts/migrate_commission_plans.py

from apps.commission_plans.models import CommissionPlan as OldPlan
from apps.commissions.models import CommissionPlan as NewPlan, CommissionPlanTier

def migrate_commission_plans():
    """
    迁移 commission_plans 到 commissions
    
    策略：
    1. 读取所有活跃的 commission_plans.CommissionPlan
    2. 转换为 commissions.CommissionPlan 格式
    3. 创建新记录
    4. 标记旧记录为 migrated
    """
    old_plans = OldPlan.objects.filter(is_active=True)
    
    for old_plan in old_plans:
        # 检查是否已迁移
        existing = NewPlan.objects.filter(
            site__site_id=old_plan.site_id,
            name=old_plan.name
        ).first()
        
        if existing:
            print(f"Skip: {old_plan.name} already exists")
            continue
        
        # 创建新方案
        new_plan = NewPlan.objects.create(
            site_id=old_plan.site_id,  # 需要获取 Site 实例
            name=old_plan.name,
            description=f"Migrated from v{old_plan.version}",
            max_levels=old_plan.tiers.count(),
            is_default=False,  # 需要手动设置默认
            is_active=True
        )
        
        # 迁移层级配置
        for old_tier in old_plan.tiers.all():
            CommissionPlanTier.objects.create(
                plan=new_plan,
                level=old_tier.level,
                rate_percent=old_tier.rate_percent,
                hold_days=old_tier.hold_days,
                min_order_amount=old_tier.min_sales  # 字段名映射
            )
        
        print(f"Migrated: {old_plan.name} → {new_plan.plan_id}")

if __name__ == '__main__':
    migrate_commission_plans()
```

#### Step 2: 更新快照服务

**文件**: `backend/apps/orders_snapshots/services.py`

**改动**: 已指向 `apps.commission_plans.models.CommissionPlan`，需改为：
```python
# 从推荐的模型导入
from apps.commissions.models import CommissionPlan
```

#### Step 3: 更新路由

**当前路由**:
```
/api/v1/commission-plans/  (commission_plans app)
/api/v1/commissions/plans/ (commissions app)
```

**迁移后**:
```
/api/v1/commissions/plans/  (主要端点)
/api/v1/commission-plans/   (保留，重定向或返回废弃警告)
```

#### Step 4: 标记废弃

在所有 commission_plans 文件顶部添加：
```python
import warnings
warnings.warn(
    "This module is deprecated. Use apps.commissions instead.",
    DeprecationWarning
)
```

---

## API 迁移对照

### 旧端点（commission_plans）

```python
# 已废弃
GET    /api/v1/commission-plans/
POST   /api/v1/commission-plans/
PATCH  /api/v1/commission-plans/{id}/activate/
```

### 新端点（commissions）⭐ 推荐

```python
GET    /api/v1/commissions/plans/
POST   /api/v1/commissions/plans/
POST   /api/v1/commissions/plans/{id}/set-default/
PUT    /api/v1/commissions/plans/{id}/
DELETE /api/v1/commissions/plans/{id}/
```

**主要区别**:
1. 路径：`commission-plans` → `commissions/plans`
2. 默认方案：新系统使用 `set-default` action
3. 软删除：新系统的 DELETE 为软删除

---

## 前端迁移指南

### 修改 API 调用路径

**旧代码**:
```javascript
// ❌ 废弃
const response = await fetch('/api/v1/commission-plans/', {
  method: 'POST',
  body: JSON.stringify(planData)
});
```

**新代码**:
```javascript
// ✅ 推荐
const response = await fetch('/api/v1/commissions/plans/', {
  method: 'POST',
  body: JSON.stringify(planData)
});
```

### 字段映射

| 旧字段 (commission_plans) | 新字段 (commissions) | 说明 |
|---------------------------|----------------------|------|
| `plan_id` | `plan_id` | 相同 |
| `site_id` | `site` | ⚠️ 改为 ForeignKey |
| `version` | - | ⚠️ 移除（通过 plan_id 区分） |
| `effective_from/to` | - | ⚠️ 移除（可后续补充） |
| `tiers.min_sales` | `tiers.min_order_amount` | ⚠️ 字段名不同 |
| `tiers.diff_cap_percent` | - | ⚠️ 移除（可后续补充） |

---

## 兼容性策略

### 向后兼容（推荐）

保留 commission_plans app，但在代码中添加废弃警告：

```python
# backend/apps/commission_plans/views.py

class CommissionPlanViewSet(viewsets.ModelViewSet):
    """
    ⚠️ DEPRECATED: This endpoint is deprecated.
    Please use /api/v1/commissions/plans/ instead.
    """
    
    def list(self, request, *args, **kwargs):
        warnings.warn(
            "commission-plans endpoint is deprecated, use /api/v1/commissions/plans/",
            DeprecationWarning
        )
        return super().list(request, *args, **kwargs)
```

### 数据保留

- ✅ 保留 commission_plans 数据库表
- ✅ 保留 API 端点（返回废弃警告）
- ✅ 新功能仅在 commissions 中开发

### 完全移除（v2.0.0+）

1. 移除 commission_plans app
2. 移除相关路由
3. 删除数据库表（在确认数据已迁移后）

---

## 注意事项

1. **RLS 策略**：两个系统都使用相同的表名 `commission_plans`，需要检查是否冲突
2. **快照兼容性**：OrderCommissionPolicySnapshot 当前指向哪个模型？
3. **测试覆盖**：确保新系统测试覆盖完整
4. **文档更新**：所有文档指向推荐系统

---

## 推荐时间线

| 阶段 | 时间 | 操作 |
|------|------|------|
| **Phase 1** | 立即 | 标记 commission_plans 为废弃 ✅ |
| **Phase 2** | v1.1.0 | 新功能仅在 commissions 开发 |
| **Phase 3** | v1.2.0 | 迁移现有数据（如有） |
| **Phase 4** | v1.3.0 | 移除 commission_plans 路由 |
| **Phase 5** | v2.0.0 | 完全移除 commission_plans app |

---

## 总结

**当前状态**:
- ⚠️ commission_plans app 已添加废弃警告
- ✅ commissions.CommissionPlan 为推荐系统
- ✅ 向后兼容策略已明确

**下一步**:
1. ✅ 新项目使用 commissions.CommissionPlan
2. ⚠️ 现有项目渐进式迁移
3. 📅 v2.0.0 完全移除旧系统


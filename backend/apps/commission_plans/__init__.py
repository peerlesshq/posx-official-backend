"""
Commission Plans App（版本化佣金配置）

⚠️ 废弃警告（Deprecation Warning）

本 app 已被标记为废弃，建议使用 apps.commissions.CommissionPlan 替代。

原因：
1. 功能重复：apps.commissions 已提供完整的佣金方案管理
2. 简化维护：避免维护两套相似的系统
3. 向后兼容：保留本 app 以支持旧代码

迁移建议：
- 新项目：使用 apps.commissions.CommissionPlan
- 旧项目：逐步迁移到 apps.commissions

计划移除时间：v2.0.0
"""
import warnings

warnings.warn(
    "apps.commission_plans is deprecated and will be removed in v2.0.0. "
    "Please use apps.commissions.CommissionPlan instead.",
    DeprecationWarning,
    stacklevel=2
)

# POSX Fixtures

## 种子数据说明

### 使用方法

```bash
# 加载所有 fixtures
python manage.py loaddata fixtures/seed_sites.json
python manage.py loaddata fixtures/seed_commission_plans.json

# 或者一次性加载
python manage.py loaddata fixtures/*.json
```

### 文件说明

#### seed_sites.json
- **NA**: 北美站点（活跃）- `na.posx.io`
- **ASIA**: 亚太站点（活跃）- `asia.posx.io`
- **EU**: 欧洲站点（未激活）- `eu.posx.io`

#### seed_commission_plans.json
- **Standard Plan v1**: 标准佣金计划（NA 站点）
  - Level 1: 12%（冻结7天）
  - Level 2: 5%（冻结7天）
  - Level 3: 3%（冻结7天）

### 注意事项

⚠️ **生产环境禁止使用**
- 这些 UUID 和数据仅供本地开发测试
- 生产环境需要通过 API 或管理后台创建数据

⚠️ **RLS 要求**
- 加载 fixtures 前确保：
  1. 迁移已运行
  2. RLS 策略已启用
  3. 使用 posx_admin 角色加载数据

### 验证

```bash
# 检查站点
python manage.py shell
>>> from apps.sites.models import Site
>>> Site.objects.all()

# 检查佣金计划
>>> from apps.commission_plans.models import CommissionPlan
>>> CommissionPlan.objects.all()
```




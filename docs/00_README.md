# POSX 文档索引与规范

> 最后更新：2025-11-11

## ⚡ 快速入口（30秒找到关键路径）

新同事必看：

| 文档                                                                 | 用途               | 阅读时间 |
| -------------------------------------------------------------------- | ------------------ | -------- |
| **[QUICK_STARTUP.md](./startup/QUICK_STARTUP.md)**                   | 🚀 快速启动指南     | 15分钟   |
| **[CONFIG_ENVIRONMENT.md](./config/CONFIG_ENVIRONMENT.md)**          | ⚙️ 环境配置完整指南 | 20分钟   |
| **[PHASE_C_ACCEPTANCE.md](./phases/PHASE_C_ACCEPTANCE.md)**          | ✅ Phase C 验收测试 | 30分钟   |
| **[CHECKLIST_PRODUCTION.md](./reports/CHECKLIST_PRODUCTION.md)**     | 📋 生产环境检查清单 | 10分钟   |
| **[SPEC_SYSTEM_ARCH_v1.0.0.md](./specs/SPEC_SYSTEM_ARCH_v1.0.0.md)** | 📐 系统架构规范     | 60分钟   |

---

## 📋 目录结构

```
docs/
├── 00_README.md            # 本文件（索引页）
├── AI_CONTEXT.md           # AI 上下文文档
├── DEVELOPMENT.md          # 开发指南
├── config/                 # 配置相关文档（12个）
├── deployment/             # 部署文档（2个）
├── guides/                 # 迁移与操作指南（1个）
├── phases/                 # Phase 开发文档（17个）
├── reports/                # 报告与检查清单
│   ├── CHECKLIST_*.md      # 检查清单（5个）
│   ├── REPORT_*.md         # 活跃报告（约15个）
│   ├── CHANGELOG.md        # 变更日志
│   └── archive/            # 历史归档（35+个）
├── retool/                 # Retool 集成文档（4个）
├── specs/                  # 系统规范与架构（8个）
├── startup/                # 快速启动指南（5个）
└── templates/              # 文档模板（3个）
```

---

## 📖 命名规范

所有文档必须遵循以下命名前缀（大写+下划线）：

| 前缀            | 用途            | 示例                                  |
| --------------- | --------------- | ------------------------------------- |
| `PHASE_*`       | Phase 开发文档  | `PHASE_C_IMPLEMENTATION.md`           |
| `CONFIG_*`      | 配置文档        | `CONFIG_STRIPE.md`, `CONFIG_AUTH0.md` |
| `SETUP_*`       | 安装/初始化指南 | `SETUP_ENVIRONMENT.md`                |
| `SPEC_*`        | 规范/架构文档   | `SPEC_SYSTEM_ARCH_v1.0.0.md`          |
| `REPORT_*`      | 汇总/报告       | `REPORT_VERIFICATION.md`              |
| `CHECKLIST_*`   | 检查清单        | `CHECKLIST_PRODUCTION.md`             |
| `QUICK_*`       | 快速指引        | `QUICK_STARTUP.md`                    |
| `GUIDE_*`       | 操作指南        | `GUIDE_MIGRATION_COMMISSION_PLANS.md` |
| `DEPLOYMENT_*`  | 部署文档        | `DEPLOYMENT_REFERRAL_SYSTEM.md`       |

---

## 📚 文档分类索引

### 🚀 Startup（快速启动）

- [QUICK_STARTUP.md](./startup/QUICK_STARTUP.md) - 快速启动指南
- [QUICK_ENV_SETUP.md](./startup/QUICK_ENV_SETUP.md) - 环境快速配置
- [QUICK_NEXT_STEPS.md](./startup/QUICK_NEXT_STEPS.md) - 下一步操作指南
- [GUIDE_STARTUP_AND_TEST.md](./startup/GUIDE_STARTUP_AND_TEST.md) - 完整启动和测试指南

### ⚙️ Config（配置）

- [CONFIG_ENVIRONMENT.md](./config/CONFIG_ENVIRONMENT.md) - 环境配置总览
- [CONFIG_ENV_SETUP.md](./config/CONFIG_ENV_SETUP.md) - 环境变量设置
- [CONFIG_ENV_VARIABLES.md](./config/CONFIG_ENV_VARIABLES.md) - 环境变量说明
- [CONFIG_ENV_PHASE_C.md](./config/CONFIG_ENV_PHASE_C.md) - Phase C 环境配置
- [CONFIG_PHASE_E_ENV.md](./config/CONFIG_PHASE_E_ENV.md) - Phase E 环境配置
- [CONFIG_ENV_CUSTOM.md](./config/CONFIG_ENV_CUSTOM.md) - 自定义环境配置
- [CONFIG_AUTH0.md](./config/CONFIG_AUTH0.md) - Auth0 配置
- [CONFIG_STRIPE.md](./config/CONFIG_STRIPE.md) - Stripe 配置
- [CONFIG_WEBHOOKS.md](./config/CONFIG_WEBHOOKS.md) - Webhook 配置
- [SETUP_ENVIRONMENT.md](./config/SETUP_ENVIRONMENT.md) - 环境安装指南
- [SETUP_STRIPE_CLI.md](./config/SETUP_STRIPE_CLI.md) - Stripe CLI 安装
- [SETUP_ENV_WIZARD.md](./config/SETUP_ENV_WIZARD.md) - 环境配置向导

### 🔄 Phases（开发阶段）

#### Phase B
- [PHASE_B_IMPROVEMENTS_CHECKLIST.md](./phases/PHASE_B_IMPROVEMENTS_CHECKLIST.md) - Phase B 改进清单

#### Phase C
- [PHASE_C_PLAN.md](./phases/PHASE_C_PLAN.md) - Phase C 计划
- [PHASE_C_QUICKSTART.md](./phases/PHASE_C_QUICKSTART.md) - Phase C 快速启动
- [PHASE_C_IMPLEMENTATION.md](./phases/PHASE_C_IMPLEMENTATION.md) - Phase C 实施文档
- [PHASE_C_ACCEPTANCE.md](./phases/PHASE_C_ACCEPTANCE.md) - Phase C 验收测试
- [PHASE_C_FILES_CHECKLIST.md](./phases/PHASE_C_FILES_CHECKLIST.md) - Phase C 文件清单
- [PHASE_C_DELIVERY.md](./phases/PHASE_C_DELIVERY.md) - Phase C 交付文档
- [PHASE_C_FINAL_SUMMARY.md](./phases/PHASE_C_FINAL_SUMMARY.md) - Phase C 最终总结

#### Phase D
- [PHASE_D_CORRECTIONS.md](./phases/PHASE_D_CORRECTIONS.md) - Phase D 修正
- [PHASE_D_DELIVERY.md](./phases/PHASE_D_DELIVERY.md) - Phase D 交付

#### Phase E
- [PHASE_E_FILES_QUICK_REFERENCE.md](./phases/PHASE_E_FILES_QUICK_REFERENCE.md) - Phase E 文件快速参考
- [PHASE_E_FINAL_DELIVERY.md](./phases/PHASE_E_FINAL_DELIVERY.md) - Phase E 最终交付
- [PHASE_E_IMPLEMENTATION_COMPLETE.md](./phases/PHASE_E_IMPLEMENTATION_COMPLETE.md) - Phase E 实施完成
- [PHASE_E_v2.2.1_CHANGELOG.md](./phases/PHASE_E_v2.2.1_CHANGELOG.md) - Phase E v2.2.1 变更日志
- [PHASE_E_v2.2.1_SUMMARY.md](./phases/PHASE_E_v2.2.1_SUMMARY.md) - Phase E v2.2.1 总结
- [PHASE_E_v2.2.2_FINAL.md](./phases/PHASE_E_v2.2.2_FINAL.md) - Phase E v2.2.2 最终版

#### Phase F
- [PHASE_F_IMPLEMENTATION.md](./phases/PHASE_F_IMPLEMENTATION.md) - Phase F 实施

### 📊 Reports（报告与检查清单）

#### 检查清单
- [CHECKLIST_DELIVERY.md](./reports/CHECKLIST_DELIVERY.md) - 交付检查清单
- [CHECKLIST_DEPLOYMENT_AND_MERGE.md](./reports/CHECKLIST_DEPLOYMENT_AND_MERGE.md) - 部署与合并检查清单
- [CHECKLIST_ENV_FINAL.md](./reports/CHECKLIST_ENV_FINAL.md) - 环境最终检查
- [CHECKLIST_P0_P1.md](./reports/CHECKLIST_P0_P1.md) - P0/P1 核对清单
- [CHECKLIST_PRODUCTION.md](./reports/CHECKLIST_PRODUCTION.md) - 生产环境检查

#### 活跃报告
- [REPORT_ACCEPTANCE_TESTING.md](./reports/REPORT_ACCEPTANCE_TESTING.md) - 验收测试报告
- [REPORT_AUTH0_STATUS.md](./reports/REPORT_AUTH0_STATUS.md) - Auth0 测试与状态报告
- [REPORT_AUTH0_TESTING.md](./reports/REPORT_AUTH0_TESTING.md) - Auth0 测试指南
- [REPORT_BACKEND_READINESS.md](./reports/REPORT_BACKEND_READINESS.md) - 后端就绪验证报告
- [REPORT_DELIVERY_SUMMARY.md](./reports/REPORT_DELIVERY_SUMMARY.md) - 交付总结
- [REPORT_DOWNLOAD_PACKAGE.md](./reports/REPORT_DOWNLOAD_PACKAGE.md) - 下载包说明
- [REPORT_FINAL_SUMMARY.md](./reports/REPORT_FINAL_SUMMARY.md) - 最终总结
- [REPORT_IMPLEMENTATION_SUMMARY.md](./reports/REPORT_IMPLEMENTATION_SUMMARY.md) - 实施总结
- [REPORT_IMPROVEMENTS_SUMMARY.md](./reports/REPORT_IMPROVEMENTS_SUMMARY.md) - 改进总结
- [REPORT_INIT_COMPLETE.md](./reports/REPORT_INIT_COMPLETE.md) - 初始化完成报告
- [REPORT_INIT_STATUS.md](./reports/REPORT_INIT_STATUS.md) - 初始化状态
- [REPORT_PRODUCT_FEATURE_AUDIT.md](./reports/REPORT_PRODUCT_FEATURE_AUDIT.md) - 产品功能审计报告
- [REPORT_QUICKSTART_IMPROVEMENTS.md](./reports/REPORT_QUICKSTART_IMPROVEMENTS.md) - 快速启动改进
- [REPORT_RELEASE_SUMMARY.md](./reports/REPORT_RELEASE_SUMMARY.md) - 发布总结
- [REPORT_REVIEW_ANALYSIS.md](./reports/REPORT_REVIEW_ANALYSIS.md) - 审查分析
- [REPORT_TECHNICAL_CORRECTIONS.md](./reports/REPORT_TECHNICAL_CORRECTIONS.md) - 技术修正报告
- [REPORT_VERIFICATION.md](./reports/REPORT_VERIFICATION.md) - 验证报告

#### 变更日志
- [CHANGELOG.md](./reports/CHANGELOG.md) - 变更日志

#### 📦 归档文档
历史状态报告和已完成阶段的文档存放在归档目录中：
- [archive/README.md](./reports/archive/README.md) - 归档文档说明（包含完整清单）
- 包含 35+ 个历史报告、检查清单和指南

### 📐 Specs（系统规范）

- [SPEC_SYSTEM_ARCH_v1.0.0.md](./specs/SPEC_SYSTEM_ARCH_v1.0.0.md) - 系统架构规范 v1.0.0（主版本）
- [SPEC_RLS_POLICY_v1.0.4.md](./specs/SPEC_RLS_POLICY_v1.0.4.md) - RLS 策略规范 v1.0.4
- [SPEC_ARCHITECTURE.md](./specs/SPEC_ARCHITECTURE.md) - 架构文档
- [SPEC_API_P1.md](./specs/SPEC_API_P1.md) - Phase 1 API 文档
- [SPEC_DECIMAL_PRECISION.md](./specs/SPEC_DECIMAL_PRECISION.md) - Decimal 精度标准
- [SPEC_FRAMEWORK_GUIDE.md](./specs/SPEC_FRAMEWORK_GUIDE.md) - 框架指南
- [SPEC_FRAMEWORK_v3.md](./specs/SPEC_FRAMEWORK_v3.md) - 框架规范 v3
- [SPEC_PROMO_CODE_SYSTEM.md](./specs/SPEC_PROMO_CODE_SYSTEM.md) - 促销码系统规范

### 🚀 Deployment（部署）

- [DEPLOYMENT_REFERRAL_SYSTEM.md](./deployment/DEPLOYMENT_REFERRAL_SYSTEM.md) - 推荐系统部署指南
- [NGINX_FIREBLOCKS_WEBHOOK.md](./deployment/NGINX_FIREBLOCKS_WEBHOOK.md) - Nginx Fireblocks Webhook 配置

### 📘 Guides（迁移与操作指南）

- [GUIDE_MIGRATION_COMMISSION_PLANS.md](./guides/GUIDE_MIGRATION_COMMISSION_PLANS.md) - Commission Plans 系统迁移指南

### 🔧 Retool（集成文档）

- [RETOOL_QUICK_START.md](./retool/RETOOL_QUICK_START.md) - Retool 快速启动
- [RETOOL_CONNECTION_GUIDE.md](./retool/RETOOL_CONNECTION_GUIDE.md) - Retool 连接指南
- [RETOOL_QUERY_TEMPLATES.md](./retool/RETOOL_QUERY_TEMPLATES.md) - Retool 查询模板
- [RETOOL_COMPONENT_EXAMPLES.md](./retool/RETOOL_COMPONENT_EXAMPLES.md) - Retool 组件示例

### 📐 Templates（文档模板）

- [TEMPLATE_SPEC.md](./templates/TEMPLATE_SPEC.md) - 规范文档模板
- [TEMPLATE_REPORT.md](./templates/TEMPLATE_REPORT.md) - 报告文档模板
- [TEMPLATE_CHECKLIST.md](./templates/TEMPLATE_CHECKLIST.md) - 检查清单模板

---

## 📝 贡献规范

### 文档命名规则

1. **必须使用规范前缀**：`PHASE_*`, `CONFIG_*`, `SETUP_*`, `SPEC_*`, `REPORT_*`, `CHECKLIST_*`, `QUICK_*`, `GUIDE_*`, `DEPLOYMENT_*`
2. **使用大写字母和下划线**：例如 `CONFIG_STRIPE.md`（不是 `config-stripe.md`）
3. **版本号格式**：使用 `_v1.0.0` 而非 `-v1.0.0`
4. **放入对应目录**：
   - 配置文档 → `docs/config/`
   - Phase 文档 → `docs/phases/`
   - 规范文档 → `docs/specs/`
   - 报告清单 → `docs/reports/`（历史文档 → `docs/reports/archive/`）
   - 快速指南 → `docs/startup/`
   - 部署文档 → `docs/deployment/`
   - 迁移指南 → `docs/guides/`
   - Retool 文档 → `docs/retool/`
5. **使用文档模板**：
   - 规范文档使用 [`docs/templates/TEMPLATE_SPEC.md`](./templates/TEMPLATE_SPEC.md)
   - 报告文档使用 [`docs/templates/TEMPLATE_REPORT.md`](./templates/TEMPLATE_REPORT.md)
   - 检查清单使用 [`docs/templates/TEMPLATE_CHECKLIST.md`](./templates/TEMPLATE_CHECKLIST.md)

### Pull Request 规范

- **PR 标题必须以 `[docs]` 开头**
- 示例：`[docs] Add SETUP_REDIS.md configuration guide`
- **更新 `docs/00_README.md` 索引**（如果添加新文档）
- **通过命名检查**：PR 必须通过 `python scripts/check_md_naming.py`
- **基于模板创建**：新文档应基于 `docs/templates/` 中的相应模板
- **历史文档归档**：已完成阶段的报告和状态文档应移至 `docs/reports/archive/`

### 文档质量要求

- 使用 Markdown 标准格式
- 代码块必须指定语言（如 ```python, ```bash）
- 链接使用相对路径
- 包含目录（TOC）如果文档超过 100 行
- 中英文之间添加空格（可选但推荐）

---

## 🔧 工具

### 命名校验

运行校验脚本检查文档命名是否符合规范：

```bash
python scripts/check_md_naming.py
```

### 索引更新

当添加新文档时，手动更新本文件或运行：

```bash
python scripts/update_doc_index.py
```

---

## 📞 联系

如有文档相关问题，请：
1. 查看本索引文件
2. 检查命名规范
3. 运行校验脚本
4. 提交 Issue 或 PR

---

> **文档版本**: v1.0.0  
> **维护者**: POSX Team  
> **更新频率**: 随项目开发实时更新


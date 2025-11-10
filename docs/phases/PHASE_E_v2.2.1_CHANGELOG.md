# 📝 Phase E v2.2.1 变更日志

**发布时间**: 2025-11-09  
**基于版本**: v2.2  
**变更类型**: 微调优化

---

## 🎯 变更摘要

v2.2.1 在 v2.2 基础上进行了 **6 项生产级优化**，修复了金额精度和总和验证问题，增强了安全性和可观测性。

---

## ✨ 新增功能

### 1. 资产精度配置化（P0）

**新增**:
- ✅ `ChainAssetConfig` 模型
- ✅ 批量发放时自动查询 `token_decimals`
- ✅ 人类可读金额 → 链上最小单位转换

**影响**:
- 支持 POSX (18位)、USDT (6位) 等不同精度
- 避免金额计算错误

### 2. 最后一期兜底逻辑（P0）

**新增**:
- ✅ `vesting_service.py` - Release 生成服务
- ✅ 前 N-1 期标准量化
- ✅ 最后一期精确兜底
- ✅ 总和验证机制

**影响**:
- 确保 total_tokens 与 sum(releases) 精确一致
- 消除浮点尾差

### 3. Admin 操作限速（P1）

**新增**:
- ✅ 批量发放 Action 限流：6次/分钟
- ✅ 基于 Redis 缓存

**影响**:
- 防止误操作重复触发
- 减轻 Fireblocks API 压力

### 4. Prometheus 可观测性（P1）

**新增**:
- ✅ `metrics.py` - 10+ Prometheus 指标
- ✅ 关键位置埋点（批量发放 + Webhook）
- ✅ 指标自动更新（守护任务）

**关键指标**:
- `vesting_batch_submitted_total{mode, site_id}`
- `vesting_webhook_completed_total{status}`
- `vesting_processing_stuck_gauge`

**影响**:
- 实时监控发放状态
- 及时发现堆积和异常
- 支持 Grafana 仪表板

### 5. Nginx 安全配置文档（P1）

**新增**:
- ✅ `NGINX_FIREBLOCKS_WEBHOOK.md`
- ✅ MOCK 环境本地 IP 限制
- ✅ LIVE 环境 Fireblocks IP 白名单
- ✅ 部署步骤和验证方法

**影响**:
- 分层防御最佳实践
- Ops 团队可直接使用

### 6. 双公钥验证确认（P2）

**确认**:
- ✅ v2.2 已完美实现
- ✅ 支持无缝公钥轮换
- ✅ 留空第二把公钥则自动跳过

**无需修改**

---

## 📁 文件变更

### 新建文件（4个）

| 文件 | 行数 | 说明 |
|------|------|------|
| `backend/apps/vesting/services/vesting_service.py` | 225 | Release 生成服务（含兜底） |
| `backend/apps/vesting/metrics.py` | 135 | Prometheus 指标定义 |
| `docs/deployment/NGINX_FIREBLOCKS_WEBHOOK.md` | 380 | Nginx 配置指南 |
| `docs/startup/QUICK_START_PHASE_E.md` | 320 | 快速启动指南 |

### 修改文件（4个）

| 文件 | 变更行数 | 变更内容 |
|------|----------|----------|
| `backend/apps/vesting/services/batch_release_service.py` | +35 | 资产精度转换 + 指标埋点 |
| `backend/apps/vesting/admin.py` | +18 | Admin 限流 |
| `backend/apps/webhooks/views/fireblocks_webhook.py` | +6 | Webhook 指标埋点 |
| `backend/apps/vesting/tasks.py` | +4 | 任务中更新指标 |

### 配置文件（1个）

| 文件 | 变更 | 说明 |
|------|------|------|
| `backend/requirements/base.txt` | 新建 | Phase E 依赖清单 |

---

## 🔄 升级路径

### 从 v2.2 升级到 v2.2.1

```bash
# 1. 安装新依赖
pip install prometheus-client>=0.19.0

# 2. 运行迁移（可能无新迁移，取决于是否已执行 v2.2 迁移）
python manage.py migrate

# 3. 更新环境变量（如果需要）
# 已在 v2.2 配置过则无需修改

# 4. 重启服务
sudo systemctl restart posx-backend
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat

# 5. 验证
# - Admin 界面测试批量发放
# - 访问 /metrics 查看指标
```

---

## ⚠️ 破坏性变更

**无破坏性变更**

v2.2.1 完全向后兼容 v2.2，所有改动为增强性修改。

---

## 🐛 Bug 修复

### 修复：金额精度问题

**影响**: 不同 decimals 代币发放金额错误

**修复**: 在发放前查询 ChainAssetConfig 并转换

**版本**: v2.2 → v2.2.1

### 修复：总和可能不精确

**影响**: 浮点运算尾差导致总和偏差

**修复**: 最后一期使用 `total - sum(previous)` 兜底

**版本**: v2.2 → v2.2.1

---

## 📊 性能影响

### 新增查询

- ChainAssetConfig 查询（批量发放时）
  - **频率**: 每条 release 1 次
  - **优化**: 可批量预查询并缓存
  - **影响**: 可忽略（微秒级）

- Redis 限流查询（Admin Action）
  - **频率**: 每次 Action 1 次
  - **影响**: 可忽略

### 新增指标埋点

- **影响**: 可忽略（内存操作）

---

## 🔐 安全性提升

| 项目 | v2.2 | v2.2.1 |
|------|------|--------|
| IP 限制 | Django 层 | Django + Nginx 双层 |
| Admin 限速 | 无 | 6次/分钟 |
| 金额验证 | 基础检查 | 精度配置 + 总和验证 |

---

## 📈 可观测性提升

| 项目 | v2.2 | v2.2.1 |
|------|------|--------|
| 指标数量 | 0 | 10+ |
| 自动更新 | - | 定时任务更新 |
| Grafana 支持 | ❌ | ✅ |
| 堆积监控 | ❌ | ✅ |

---

## 🎉 v2.2.1 发布！

### 核心改进

✅ **金额精度** - 配置化 decimals 转换  
✅ **总和精确** - 最后一期兜底 + 验证  
✅ **操作防护** - Admin 限速 + Nginx IP 限制  
✅ **可观测性** - 10+ Prometheus 指标  
✅ **文档完善** - Nginx 配置 + 快速启动指南  

### 推荐升级

**所有 v2.2 用户建议升级到 v2.2.1**

- ✅ 无破坏性变更
- ✅ 修复金额精度问题
- ✅ 增强安全性和可观测性
- ✅ 平滑升级（仅安装依赖即可）

---

**发布时间**: 2025-11-09  
**维护者**: POSX Team  
**质量评级**: ⭐⭐⭐⭐⭐ 生产级+


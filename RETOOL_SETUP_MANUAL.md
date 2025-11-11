# POSX Framework - Retool 运营后台设置手册

**版本**: v1.0  
**适用系统**: POSX Framework v1.0.1  
**更新日期**: 2025-11-11  
**预计设置时间**: 3-4 小时

---

## 📚 手册说明

本手册将指导您从零开始配置 Retool 运营后台，对接 POSX Framework 的所有管理功能。

### 手册结构
- **第 0 章**: 基础设置（30 分钟）- 一次性配置
- **第 1-10 章**: 10 个核心功能模块（各 15-25 分钟）
- **附录 A-F**: 参考资料和模板

### 前置要求
- ✅ POSX Framework 后端已部署并运行
- ✅ 拥有 Retool 账号（Cloud 或 Self-hosted）
- ✅ 拥有 Auth0 管理员账号（获取 JWT Token）
- ✅ 了解基本的 REST API 概念

---

## 第 0 章：基础设置（一次性配置）

### 步骤 0.1：登录 Retool 并创建 App

1. **登录 Retool**
   - 访问 `https://your-org.retool.com`
   - 使用您的 Retool 账号登录

2. **创建新 App**
   - 点击左侧菜单 `Apps` → `Create new` → `App`
   - 命名: `POSX Operations Dashboard`
   - 选择模板: `Blank app`

---

### 步骤 0.2：配置 REST API Resource（全局数据源）

1. **打开 Resources 面板**
   - 点击左下角 `⚙️ Resources`
   - 点击 `Create new` → `Resource`
   - 选择 `REST API`

2. **配置基础信息**
   ```
   Name: POSX API
   Base URL: 
     - Dev: http://localhost:8000
     - Demo: https://demo-api.posx.com
     - Prod: https://api.posx.com
   ```

3. **配置认证方式**
   - Authentication: `Bearer token`
   - Token: `{{ globalAdminToken.value }}`
   
   > 💡 稍后我们会设置 `globalAdminToken` 变量

4. **配置 Headers（重要！）**
   - 点击 `Headers` 标签
   - 添加以下 Headers：
   
   | Key | Value |
   |-----|-------|
   | `X-Site-Code` | `{{ globalSiteCode.value }}` |
   | `Content-Type` | `application/json` |
   | `Accept` | `application/json` |

5. **测试连接**
   - 点击 `Test connection`
   - 应该显示连接成功

6. **保存 Resource**
   - 点击 `Save`

---

### 步骤 0.3：设置全局变量

1. **创建全局变量**
   - 在编辑器左侧点击 `Code` 图标
   - 点击 `+ New` → `Variable`
   - 创建以下变量：

   **变量 1: baseUrl**
   ```javascript
   Name: baseUrl
   Type: Simple
   Default value: "http://localhost:8000"  // 根据环境调整
   ```

   **变量 2: globalSiteCode**
   ```javascript
   Name: globalSiteCode
   Type: Simple
   Default value: "NA"  // 或 "ASIA"
   ```

   **变量 3: globalAdminToken**
   ```javascript
   Name: globalAdminToken
   Type: Simple
   Default value: ""  // 稍后填入 JWT Token
   ```

2. **获取 Auth0 JWT Token**
   
   方法 1 - 使用测试端点：
   ```bash
   # 调用后端认证 API
   curl -X POST http://localhost:8000/api/v1/auth/wallet/ \
     -H "Content-Type: application/json" \
     -d '{
       "wallet_address": "0x...",
       "signature": "..."
     }'
   ```

   方法 2 - 从浏览器开发者工具获取：
   - 打开前端应用并登录
   - 打开浏览器开发者工具（F12）
   - 切换到 `Application` → `Local Storage`
   - 复制 `access_token` 或 `jwt_token`

3. **填入 Token**
   - 复制获取的 JWT Token
   - 粘贴到 `globalAdminToken` 变量的 `Default value`
   - 保存

---

### 步骤 0.4：配置统一错误处理

1. **创建错误处理函数**
   - 点击 `+ New` → `JavaScript Query`
   - 命名: `handleApiError`
   - 代码：

   ```javascript
   // 统一错误处理函数
   function handleApiError(error) {
     const status = error?.response?.status;
     const message = error?.response?.data?.message || error?.message;
     
     switch(status) {
       case 401:
         utils.showNotification({
           title: '认证失效',
           description: '请重新登录获取 Token',
           notificationType: 'error',
           duration: 5
         });
         break;
       
       case 429:
         utils.showNotification({
           title: '请求过快',
           description: '请稍后重试',
           notificationType: 'warning',
           duration: 3
         });
         break;
       
       case 500:
       case 502:
       case 503:
         utils.showNotification({
           title: '服务器错误',
           description: message || '请联系技术支持',
           notificationType: 'error',
           duration: 5
         });
         break;
       
       default:
         utils.showNotification({
           title: '请求失败',
           description: message || '未知错误',
           notificationType: 'error',
           duration: 3
         });
     }
   }
   
   // 导出函数
   return { handleApiError };
   ```

2. **在查询中使用**
   - 在每个 API 查询的 `Error` 事件处理器中调用：
   ```javascript
   handleApiError.data.handleApiError(error)
   ```

---

### 步骤 0.5：测试基础配置

1. **创建测试查询**
   - 点击 `+ New` → `Resource query`
   - 选择 `POSX API` Resource
   - 配置：
   
   ```
   Action type: GET
   URL: {{ baseUrl.value }}/ready/
   Headers: (自动从 Resource 继承)
   ```

2. **运行测试**
   - 点击 `Run query`
   - 应该返回：
   ```json
   {
     "status": "healthy",
     "checks": {
       "database": "ok",
       "redis": "ok",
       "migrations": "ok",
       "rls": "ok"
     }
   }
   ```

3. **验证成功标志**
   - ✅ Status Code: 200
   - ✅ Response 包含 "healthy"
   - ✅ 所有 checks 均为 "ok"

---

## 第 1 章：概览仪表盘（Ops Home）

### 页面目标
创建运营总览页面，显示关键业务指标和异常监控。

---

### 步骤 1.1：创建新页面

1. **创建页面**
   - 在 App 中点击 `+ New` → `Page`
   - 命名: `Dashboard`
   - 设置为首页（Home page）

2. **页面布局**
   - 拖拽 `Container` 组件到画布
   - 设置 Container 为 4 列布局（Grid columns: 4）

---

### 步骤 1.2：创建概览报表查询

1. **新建查询**
   - 点击 `+ New` → `Resource query`
   - 命名: `overviewReport`
   - 配置：

   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/admin/reports/overview/
   
   Query params:
     site_code: {{ globalSiteCode.value }}
     date_from: {{ dateRangeFilter.value.start }}  // 后续创建
     date_to: {{ dateRangeFilter.value.end }}
   
   Headers: (自动继承)
   ```

2. **配置自动运行**
   - Advanced 标签下勾选 `Run query on page load`
   - 设置刷新间隔: `5 minutes`

---

### 步骤 1.3：创建日期范围筛选器

1. **添加 Date Range Picker**
   - 拖拽 `Date Range` 组件到页面顶部
   - 命名: `dateRangeFilter`
   - 配置：
   
   ```javascript
   Default value: 
     Start: {{ moment().startOf('month').toDate() }}
     End: {{ moment().toDate() }}
   
   Format: YYYY-MM-DD
   ```

2. **添加刷新按钮**
   - 拖拽 `Button` 组件到日期选择器旁边
   - Text: `🔄 刷新`
   - 事件: `onClick` → `overviewReport.trigger()`

---

### 步骤 1.4：创建 KPI 卡片组

1. **订单统计卡片**
   - 拖拽 `Statistic` 组件
   - 配置：
   
   ```javascript
   Label: "总订单数"
   Value: {{ overviewReport.data.total_orders || 0 }}
   Primary color: Blue
   ```

2. **销售额卡片**
   - 拖拽 `Statistic` 组件
   - 配置：
   
   ```javascript
   Label: "总销售额 (USD)"
   Value: {{ '$' + (overviewReport.data.total_sales || '0.00') }}
   Primary color: Green
   Format: Currency
   ```

3. **佣金统计卡片**
   - 拖拽 `Statistic` 组件
   - 配置：
   
   ```javascript
   Label: "待结算佣金"
   Value: {{ '$' + (overviewReport.data.total_commissions_pending || '0.00') }}
   Primary color: Orange
   ```

4. **活跃代理卡片**
   - 拖拽 `Statistic` 组件
   - 配置：
   
   ```javascript
   Label: "活跃代理"
   Value: {{ overviewReport.data.active_agents || 0 }}
   Primary color: Purple
   ```

---

### 步骤 1.5：创建异常监控区

1. **创建异常查询**
   - 新建查询: `anomalyReport`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/admin/reports/anomalies/
   
   Advanced:
     Run on page load: ✓
     Refresh interval: 5 minutes
   ```

2. **添加异常提示卡片**
   - 拖拽 `Container` 组件
   - 背景色: Light Red (如果有异常)
   - 添加 4 个 `Text` 组件显示：
   
   ```javascript
   卡住的佣金: {{ anomalyReport.data.stuck_commissions || 0 }}
   失败的分配: {{ anomalyReport.data.failed_allocations || 0 }}
   争议订单: {{ anomalyReport.data.disputed_orders || 0 }}
   待审核提现: {{ anomalyReport.data.pending_withdrawals || 0 }}
   ```

3. **添加告警逻辑**
   - Container 的 `Hidden` 属性设置为：
   ```javascript
   {{
     (anomalyReport.data.stuck_commissions || 0) === 0 &&
     (anomalyReport.data.failed_allocations || 0) === 0 &&
     (anomalyReport.data.disputed_orders || 0) === 0 &&
     (anomalyReport.data.pending_withdrawals || 0) === 0
   }}
   ```

---

### 步骤 1.6：测试 Dashboard

1. **运行所有查询**
   - 点击右上角 `▶ Preview`
   - 验证所有 KPI 卡片显示正常

2. **验证数据刷新**
   - 修改日期范围
   - 点击刷新按钮
   - 确认数据更新

---

## 第 2 章：用户管理（Users）

### 页面目标
管理所有用户账户，查看推荐关系，管理代理身份。

---

### 步骤 2.1：创建用户列表页面

1. **创建新页面**
   - 点击 `+ New` → `Page`
   - 命名: `Users`

2. **创建用户列表查询**
   - 命名: `usersList`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/users/
   
   Query params:
     page: {{ usersTable.pageIndex + 1 }}
     page_size: {{ usersTable.pageSize }}
     site_code: {{ siteFilter.value }}
     is_agent: {{ isAgentFilter.value }}
     has_referrer: {{ hasReferrerFilter.value }}
   ```

---

### 步骤 2.2：添加用户列表表格

1. **拖拽 Table 组件**
   - 命名: `usersTable`
   - Data source: `{{ usersList.data.results }}`

2. **配置列**
   
   | 列名 | 数据路径 | 格式 | 说明 |
   |------|---------|------|------|
   | User ID | `user_id` | UUID（隐藏前缀） | `{{ currentRow.user_id.slice(-8) }}` |
   | Email | `email` | Text | - |
   | Wallet | `wallet_address` | Text | `{{ currentRow.wallet_address?.slice(0,10) }}...` |
   | Site | `site_code` | Badge | - |
   | Referrer | `referrer_email` | Text | - |
   | Is Active | `is_active` | Toggle | - |
   | Created | `created_at` | Datetime | `{{ moment(currentRow.created_at).format('YYYY-MM-DD HH:mm') }}` |

3. **配置分页**
   ```javascript
   Pagination type: Server-side
   Total row count: {{ usersList.data.count }}
   Page size options: [20, 50, 100]
   ```

---

### 步骤 2.3：添加筛选器

1. **站点筛选器**
   - 拖拽 `Select` 组件
   - 命名: `siteFilter`
   - Options: `['all', 'NA', 'ASIA']`
   - Default value: `'all'`
   - 事件: `onChange` → `usersList.trigger()`

2. **代理状态筛选器**
   - 拖拽 `Checkbox` 组件
   - 命名: `isAgentFilter`
   - Label: `仅显示代理`
   - 事件: `onChange` → `usersList.trigger()`

3. **推荐关系筛选器**
   - 拖拽 `Checkbox` 组件
   - 命名: `hasReferrerFilter`
   - Label: `仅显示有推荐人的用户`
   - 事件: `onChange` → `usersList.trigger()`

---

### 步骤 2.4：添加操作按钮

1. **查看详情按钮**
   - 在 Table 中添加 Action 列
   - 添加 Button: `查看详情`
   - 事件: 
   ```javascript
   onClick → 打开 Modal (userDetailModal)
   ```

2. **创建详情 Modal**
   - 拖拽 `Modal` 组件
   - 命名: `userDetailModal`
   - 显示用户完整信息
   - 包含推荐关系树

---

## 第 3 章：代理管理（Agents）

### 页面目标
管理代理账户，查看推荐树，处理提现，查看报表。

---

### 步骤 3.1：创建代理列表页面

1. **创建新页面**
   - 命名: `Agents`

2. **创建代理仪表盘查询**
   - 命名: `agentDashboard`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/agents/dashboard/
   
   Headers: (继承全局)
   ```

---

### 步骤 3.2：创建代理列表查询

1. **新建查询**
   - 命名: `agentsList`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/agents/
   
   Query params:
     page: {{ agentsTable.pageIndex + 1 }}
     page_size: 50
     site_code: {{ globalSiteCode.value }}
     min_downlines: {{ minDownlinesFilter.value }}
     min_balance: {{ minBalanceFilter.value }}
   ```

---

### 步骤 3.3：添加代理列表表格

1. **拖拽 Table 组件**
   - 命名: `agentsTable`
   - Data: `{{ agentsList.data.results }}`

2. **配置列**
   
   | 列名 | 数据路径 | 格式 | 说明 |
   |------|---------|------|------|
   | Agent ID | `agent_id` | Text | 短 UUID |
   | Email | `email` | Text | - |
   | Level | `level` | Badge | L1/L2/L3... |
   | Upline | `upline_email` | Text | 上级邮箱 |
   | Downlines | `total_downlines` | Number | 下级数量 |
   | Available | `available_balance` | Currency | 可用余额 |
   | Frozen | `frozen_balance` | Currency | 冻结余额 |
   | Withdrawn | `total_withdrawn` | Currency | 累计提现 |
   | Active | `is_active` | Boolean | 激活状态 |

3. **添加 Action 列**
   - Button 1: `查看推荐树`
   - Button 2: `查看余额`
   - Button 3: `申请提现`

---

### 步骤 3.4：创建推荐树查询

1. **新建查询**
   - 命名: `agentDownlines`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/agents/downlines/
   
   Query params:
     agent_id: {{ agentsTable.selectedRow.data.agent_id }}
     max_depth: 10
   
   Run trigger: 
     Manual (仅在点击"查看推荐树"时运行)
   ```

2. **创建推荐树 Modal**
   - 拖拽 `Modal` 组件
   - 命名: `downlineTreeModal`
   - 添加 `Tree` 或 `Table` 组件显示层级关系
   - Data: `{{ agentDownlines.data.downlines }}`

---

### 步骤 3.5：创建余额查询

1. **新建查询**
   - 命名: `agentBalance`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/agents/balance/
   
   Query params:
     agent_id: {{ agentsTable.selectedRow.data.agent_id }}
   ```

2. **创建余额详情 Modal**
   - 命名: `balanceDetailModal`
   - 显示字段：
     - 可用余额: `{{ agentBalance.data.available_balance }}`
     - 冻结余额: `{{ agentBalance.data.frozen_balance }}`
     - 已提现: `{{ agentBalance.data.total_withdrawn }}`
     - 待结算: `{{ agentBalance.data.pending_commissions }}`

---

### 步骤 3.6：创建提现功能

1. **新建提现申请查询**
   - 命名: `createWithdrawal`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: POST
   URL: {{ baseUrl.value }}/api/v1/agents/withdrawals/
   
   Body:
   {
     "agent_id": "{{ agentsTable.selectedRow.data.agent_id }}",
     "amount": "{{ withdrawalAmountInput.value }}"
   }
   
   Run trigger: Manual
   ```

2. **创建提现 Form**
   - 拖拽 `Modal` 组件: `withdrawalModal`
   - 添加 `Number Input`: `withdrawalAmountInput`
   - 添加 `Button`: `提交提现申请`
   - Button 事件: `onClick` → `createWithdrawal.trigger()`

---

## 第 4 章：佣金中心（Commissions）

### 页面目标
管理所有佣金记录，批量结算，查看对账报表。

---

### 步骤 4.1：创建佣金列表页面

1. **创建新页面**
   - 命名: `Commissions`

2. **创建佣金列表查询**
   - 命名: `commissionsList`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/commissions/
   
   Query params:
     page: {{ commissionsTable.pageIndex + 1 }}
     page_size: 50
     status: {{ statusFilter.value }}
     level: {{ levelFilter.value }}
     date_from: {{ dateFilter.value.start }}
     date_to: {{ dateFilter.value.end }}
   ```

---

### 步骤 4.2：添加佣金列表表格

1. **拖拽 Table 组件**
   - 命名: `commissionsTable`
   - Data: `{{ commissionsList.data.results }}`
   - 启用行选择: `✓ Enable selection`

2. **配置列**
   
   | 列名 | 数据路径 | 格式 | 说明 |
   |------|---------|------|------|
   | Commission ID | `commission_id` | Text | 短 UUID |
   | Order ID | `order_id` | Link | 链接到订单详情 |
   | Agent Email | `agent_email` | Text | - |
   | Level | `level` | Badge | L1(12%)/L2(4%) |
   | Rate % | `rate_percent` | Number | 2 位小数 |
   | Amount USD | `commission_amount_usd` | Currency | `$` 前缀 |
   | Status | `status` | Tag | hold🟡/ready🟢/paid✅/cancelled❌ |
   | Hold Until | `hold_until` | Datetime | 仅 status=hold 显示 |
   | Paid At | `paid_at` | Datetime | 仅 status=paid 显示 |

3. **状态列颜色配置**
   ```javascript
   Background color:
   {{
     currentRow.status === 'hold' ? 'yellow' :
     currentRow.status === 'ready' ? 'green' :
     currentRow.status === 'paid' ? 'blue' :
     'gray'
   }}
   ```

---

### 步骤 4.3：添加筛选器

1. **状态筛选器**
   - `Select`: `statusFilter`
   - Options: `['all', 'hold', 'ready', 'paid', 'cancelled']`
   - Default: `'ready'`

2. **层级筛选器**
   - `Select`: `levelFilter`
   - Options: `['all', '1', '2', '3']`
   - Labels: `['全部', 'L1 (12%)', 'L2 (4%)', 'L3+']`

3. **日期范围**
   - `Date Range`: `dateFilter`
   - Default: 本月

---

### 步骤 4.4：创建批量结算功能

1. **新建批量结算查询**
   - 命名: `batchSettleCommissions`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: POST
   URL: {{ baseUrl.value }}/api/v1/commissions/batch-settle/
   
   Body:
   {
     "commission_ids": {{ commissionsTable.selectedRows.map(r => r.commission_id) }}
   }
   
   Success event:
     commissionsList.trigger()
     utils.showNotification({
       title: '批量结算成功',
       description: `已结算 ${commissionsTable.selectedRows.length} 条佣金`,
       notificationType: 'success'
     })
   ```

2. **添加批量结算按钮**
   - 拖拽 `Button` 到表格上方
   - Text: `批量结算选中项`
   - Disabled: `{{ commissionsTable.selectedRows.length === 0 }}`
   - 事件: `onClick` → `batchSettleCommissions.trigger()`

---

### 步骤 4.5：创建佣金对账报表

1. **新建对账报表查询**
   - 命名: `reconciliationReport`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/admin/reports/reconciliation/
   
   Query params:
     period: {{ moment().format('YYYY-MM') }}
     site_code: {{ globalSiteCode.value }}
   ```

2. **添加报表区域**
   - 拖拽 `Container` 到页面底部
   - 添加多个 `Statistic` 显示：
     - 本期生成: `{{ reconciliationReport.data.total_generated }}`
     - 已支付: `{{ reconciliationReport.data.total_paid }}`
     - 待结算: `{{ reconciliationReport.data.total_pending }}`
     - 已取消: `{{ reconciliationReport.data.total_cancelled }}`

---

## 第 5 章：产品/档位配置器（Tiers）

### 页面目标
管理产品档位，配置价格和库存，设置促销活动。

---

### 步骤 5.1：创建产品列表页面

1. **创建新页面**
   - 命名: `Tiers`

2. **创建产品列表查询**
   - 命名: `tiersList`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/tiers/
   
   Query params:
     page: {{ tiersTable.pageIndex + 1 }}
     page_size: 20
   ```

---

### 步骤 5.2：添加产品列表表格

1. **拖拽 Table 组件**
   - 命名: `tiersTable`
   - Data: `{{ tiersList.data.results }}`

2. **配置列**
   
   | 列名 | 数据路径 | 格式 | 说明 |
   |------|---------|------|------|
   | Tier ID | `tier_id` | Text | 短 UUID |
   | Name | `name` | Text | - |
   | Price USD | `price_usd` | Currency | `$` 格式 |
   | Inventory | `inventory_available` | Number | 当前库存 |
   | Sold | `inventory_sold` | Number | 已售数量 |
   | Tokens/Unit | `tokens_per_unit` | Number | 每单位代币数 |
   | Promotion | `has_active_promotion` | Tag | 是否有促销 |
   | Active | `is_active` | Toggle | 启用状态 |

---

### 步骤 5.3：创建库存调整功能

1. **新建库存调整查询**
   - 命名: `adjustInventory`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: POST
   URL: {{ baseUrl.value }}/api/v1/admin/tiers/{{ tiersTable.selectedRow.data.tier_id }}/adjust-inventory/
   
   Body:
   {
     "adjustment": {{ inventoryAdjustmentInput.value }},
     "reason": "{{ inventoryReasonInput.value }}"
   }
   
   Success event:
     tiersList.trigger()
     inventoryModal.close()
   ```

2. **创建库存调整 Modal**
   - 命名: `inventoryModal`
   - 添加组件：
     - `Number Input`: `inventoryAdjustmentInput` (可正可负)
     - `Text Input`: `inventoryReasonInput` (调整原因)
     - `Button`: `确认调整` → `adjustInventory.trigger()`

---

### 步骤 5.4：创建产品创建/编辑表单

1. **新建创建产品查询**
   - 命名: `createTier`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: POST
   URL: {{ baseUrl.value }}/api/v1/admin/tiers/
   
   Body:
   {
     "name": "{{ tierNameInput.value }}",
     "price_usd": "{{ tierPriceInput.value }}",
     "tokens_per_unit": "{{ tierTokensInput.value }}",
     "inventory_total": {{ tierInventoryInput.value }},
     "is_active": {{ tierActiveInput.value }}
   }
   ```

2. **创建产品表单 Modal**
   - 命名: `tierFormModal`
   - 添加所有必需字段的输入组件
   - 提交按钮触发 `createTier.trigger()`

---

### 步骤 5.5：查看产品统计

1. **新建统计查询**
   - 命名: `tierStats`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/admin/tiers/{{ tiersTable.selectedRow.data.tier_id }}/stats/
   ```

2. **创建统计 Modal**
   - 显示销售数据、转化率等

---

## 第 6 章：站点配置（Sites）

### 页面目标
管理多站点配置，配置链资产，查看站点统计。

---

### 步骤 6.1：创建站点列表页面

1. **创建新页面**
   - 命名: `Sites`

2. **创建站点列表查询**
   - 命名: `sitesList`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/admin/sites/
   ```

---

### 步骤 6.2：添加站点列表表格

1. **拖拽 Table 组件**
   - 命名: `sitesTable`
   - Data: `{{ sitesList.data.results }}`

2. **配置列**
   
   | 列名 | 数据路径 | 格式 |
   |------|---------|------|
   | Site ID | `site_id` | Text |
   | Site Code | `site_code` | Badge |
   | Chain | `primary_chain` | Tag |
   | KYC Required | `kyc_required` | Boolean |
   | Active | `is_active` | Toggle |
   | Created | `created_at` | Datetime |

---

### 步骤 6.3：创建链资产配置

1. **新建资产列表查询**
   - 命名: `chainAssetsList`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/admin/sites/assets/
   ```

2. **添加资产配置表格**
   - 显示字段: chain, token_symbol, token_decimals, fireblocks_asset_id
   - 操作: 编辑、激活/禁用

3. **新建资产创建查询**
   - 命名: `createChainAsset`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: POST
   URL: {{ baseUrl.value }}/api/v1/admin/chain-assets/create/
   
   Body:
   {
     "chain": "{{ chainInput.value }}",
     "token_symbol": "{{ symbolInput.value }}",
     "token_decimals": {{ decimalsInput.value }},
     "fireblocks_asset_id": "{{ assetIdInput.value }}",
     "fireblocks_vault_id": "{{ vaultIdInput.value }}",
     "address_type": "{{ addressTypeInput.value }}"
   }
   ```

---

### 步骤 6.4：站点统计查询

1. **新建统计查询**
   - 命名: `siteStats`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/admin/sites/{{ sitesTable.selectedRow.data.site_id }}/stats/
   ```

2. **显示统计数据**
   - 订单数、用户数、销售额等

---

## 第 7 章：订单管理（Orders）

### 页面目标
查看所有订单，管理促销码，查看订单快照。

---

### 步骤 7.1：创建订单列表页面

1. **创建新页面**
   - 命名: `Orders`

2. **创建订单列表查询**
   - 命名: `ordersList`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/orders/
   
   Query params:
     page: {{ ordersTable.pageIndex + 1 }}
     page_size: 50
     status: {{ orderStatusFilter.value }}
     date_from: {{ orderDateFilter.value.start }}
     date_to: {{ orderDateFilter.value.end }}
   ```

---

### 步骤 7.2：添加订单列表表格

1. **拖拽 Table 组件**
   - 命名: `ordersTable`
   - Data: `{{ ordersList.data.results }}`

2. **配置列**
   
   | 列名 | 数据路径 | 格式 | 说明 |
   |------|---------|------|------|
   | Order ID | `order_id` | Text | 短 UUID |
   | Buyer | `buyer_email` | Text | - |
   | Tier | `tier_name` | Text | - |
   | Quantity | `quantity` | Number | - |
   | Amount USD | `final_price_usd` | Currency | 最终价格 |
   | Discount | `total_discount_usd` | Currency | 总折扣 |
   | Status | `status` | Tag | pending/paid/failed/cancelled |
   | Payment ID | `stripe_payment_intent_id` | Text | Stripe ID |
   | Created | `created_at` | Datetime | - |

3. **状态列配色**
   ```javascript
   {{
     currentRow.status === 'pending' ? 'orange' :
     currentRow.status === 'paid' ? 'green' :
     currentRow.status === 'failed' ? 'red' :
     'gray'
   }}
   ```

---

### 步骤 7.3：添加筛选器

1. **状态筛选**
   - `Select`: `orderStatusFilter`
   - Options: `['all', 'pending', 'paid', 'failed', 'cancelled']`

2. **日期范围**
   - `Date Range`: `orderDateFilter`

---

### 步骤 7.4：创建促销码管理

1. **新建促销码列表查询**
   - 命名: `promoCodesList`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/orders/admin/promo-codes/
   
   Query params:
     page: 1
     page_size: 50
     is_active: true
   ```

2. **添加促销码表格**
   - 显示: code, discount_type, discount_value, usage_count, max_uses
   - 操作: 激活/禁用、查看使用记录

3. **促销码使用记录查询**
   - 命名: `promoCodeUsages`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/orders/admin/promo-codes/{{ promoCodesTable.selectedRow.data.promo_id }}/usages/
   ```

---

## 第 8 章：代币分配 & 发放（Allocations + Vesting）

### 页面目标
管理代币分配记录，监控释放进度，处理异常。

---

### 步骤 8.1：创建分配列表页面

1. **创建新页面**
   - 命名: `Allocations`

2. **创建分配列表查询**
   - 命名: `allocationsList`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/allocations/
   
   Query params:
     page: {{ allocationsTable.pageIndex + 1 }}
     page_size: 50
     status: {{ allocationStatusFilter.value }}
   ```

---

### 步骤 8.2：添加分配列表表格

1. **拖拽 Table 组件**
   - 命名: `allocationsTable`
   - Data: `{{ allocationsList.data.results }}`

2. **配置列**
   
   | 列名 | 数据路径 | 格式 |
   |------|---------|------|
   | Allocation ID | `allocation_id` | Text |
   | Order ID | `order_id` | Link |
   | Wallet | `wallet_address` | Text |
   | Total Tokens | `token_amount` | Number (6 位小数) |
   | Released | `released_tokens` | Number |
   | Pending | `pending_tokens` | Number |
   | Progress % | `release_progress` | Progress Bar |
   | Status | `status` | Tag |

---

### 步骤 8.3：创建释放记录查询

1. **新建 VestingRelease 查询**
   - 命名: `vestingReleasesList`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/vesting-releases/
   
   Query params:
     page: {{ releasesTable.pageIndex + 1 }}
     page_size: 50
     status: {{ releaseStatusFilter.value }}
     from: {{ releaseDateFilter.value.start }}
     to: {{ releaseDateFilter.value.end }}
   ```

2. **添加释放记录表格**
   - 命名: `releasesTable`
   - Data: `{{ vestingReleasesList.data.results }}`
   - 列: release_id, user_email, period_no, release_date, amount, chain, status, fireblocks_tx_id, tx_hash

---

### 步骤 8.4：创建卡住 Release 监控

1. **新建卡住统计查询**
   - 命名: `stuckReleasesStats`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/admin/vesting/releases/stuck-stats/
   
   Advanced:
     Run on page load: ✓
     Refresh interval: 2 minutes
   ```

2. **添加监控卡片**
   - 拖拽 `Container` 到页面顶部
   - 背景色: `{{ stuckReleasesStats.data.stuck_count > 0 ? 'red' : 'green' }}`
   - 显示：
     - 卡住数量: `{{ stuckReleasesStats.data.stuck_count }}`
     - 最早卡住时间: `{{ stuckReleasesStats.data.oldest_stuck_at }}`

---

### 步骤 8.5：创建手动对账功能

1. **新建对账触发查询**
   - 命名: `triggerReconcile`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: POST
   URL: {{ baseUrl.value }}/api/v1/admin/vesting/releases/reconcile/
   
   Success event:
     utils.showNotification({
       title: '对账任务已触发',
       description: '预计 5 分钟内完成',
       notificationType: 'success'
     })
     stuckReleasesStats.trigger()  // 刷新统计
   ```

2. **添加对账按钮**
   - Text: `🔄 手动触发对账`
   - Disabled: `{{ stuckReleasesStats.data.stuck_count === 0 }}`
   - 事件: `onClick` → `triggerReconcile.trigger()`

---

## 第 9 章：通知中心（Notifications）

### 页面目标
管理系统通知，发布公告，查看未读数。

---

### 步骤 9.1：创建通知列表页面

1. **创建新页面**
   - 命名: `Notifications`

2. **创建通知列表查询**
   - 命名: `notificationsList`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/notifications/
   
   Query params:
     page: {{ notificationsTable.pageIndex + 1 }}
     page_size: 50
     unread: {{ showUnreadOnly.value }}
     category: {{ categoryFilter.value }}
     severity: {{ severityFilter.value }}
   ```

---

### 步骤 9.2：添加通知列表表格

1. **拖拽 Table 组件**
   - 命名: `notificationsTable`
   - Data: `{{ notificationsList.data.results }}`

2. **配置列**
   
   | 列名 | 数据路径 | 格式 |
   |------|---------|------|
   | ID | `notification_id` | Text |
   | Recipient Type | `recipient_type` | Badge |
   | Category | `category` | Tag |
   | Severity | `severity` | Tag (颜色编码) |
   | Title | `title` | Text |
   | Is Read | `is_read` | Boolean |
   | Visible At | `visible_at` | Datetime |
   | Created | `created_at` | Datetime |

3. **严重度颜色**
   ```javascript
   {{
     currentRow.severity === 'critical' ? 'red' :
     currentRow.severity === 'high' ? 'orange' :
     currentRow.severity === 'warning' ? 'yellow' :
     'blue'
   }}
   ```

---

### 步骤 9.3：创建未读数统计

1. **新建未读数查询**
   - 命名: `unreadCount`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/notifications/unread-count/
   
   Advanced:
     Run on page load: ✓
     Refresh interval: 1 minute
   ```

2. **添加未读数卡片**
   - `Statistic`: 显示总未读数
   - Value: `{{ unreadCount.data.total }}`
   - 按分类统计: `{{ unreadCount.data.by_category }}`
   - 按严重度统计: `{{ unreadCount.data.by_severity }}`

---

### 步骤 9.4：创建批量标记已读功能

1. **新建标记已读查询**
   - 命名: `markNotificationsRead`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: PATCH
   URL: {{ baseUrl.value }}/api/v1/notifications/mark-read/
   
   Body:
   {
     "notification_ids": {{ notificationsTable.selectedRows.map(r => r.notification_id) }},
     "mark_all": false
   }
   
   Success event:
     notificationsList.trigger()
     unreadCount.trigger()
   ```

2. **添加操作按钮**
   - Button 1: `标记选中为已读`
   - Button 2: `全部标记已读` (设置 mark_all: true)

---

### 步骤 9.5：创建公告列表

1. **新建公告查询**
   - 命名: `announcementsList`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/notifications/announcements/
   
   Query params:
     page: 1
     page_size: 20
     unread: false
   ```

2. **添加公告表格**
   - 显示站点广播类型的通知
   - 操作: 查看详情、编辑

---

## 第 10 章：系统配置 & Webhook（Config + Webhooks）

### 页面目标
管理系统配置，监控和重放 Webhook 事件。

---

### 步骤 10.1：创建系统配置页面

1. **创建新页面**
   - 命名: `Config`

2. **创建配置状态查询**
   - 命名: `allowProdTxStatus`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/admin/config/allow-prod-tx/
   
   Advanced:
     Run on page load: ✓
   ```

---

### 步骤 10.2：添加配置状态 Banner

1. **拖拽 Banner 组件**
   - 显示条件: `{{ allowProdTxStatus.data.allow_prod_tx === false }}`
   - Text: `{{ allowProdTxStatus.data.warning }}`
   - Type: `warning`
   - 显示：
     - 当前模式: `{{ allowProdTxStatus.data.fireblocks_mode }}`
     - 生产交易状态: `{{ allowProdTxStatus.data.allow_prod_tx ? '✅ 已启用' : '⚠️ 已禁用' }}`

---

### 步骤 10.3：创建 Webhook 事件列表

1. **新建 Webhook 列表查询**
   - 命名: `webhookEventsList`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/webhooks/events/
   
   Query params:
     page: {{ webhooksTable.pageIndex + 1 }}
     page_size: 50
     processing_status: {{ webhookStatusFilter.value }}
     source: {{ webhookSourceFilter.value }}
   ```

2. **添加 Webhook 表格**
   - 命名: `webhooksTable`
   - 列: event_id, source (stripe/fireblocks), event_type, processing_status, tx_id, error_message, created_at

---

### 步骤 10.4：创建 Webhook 重放功能

1. **新建重放查询**
   - 命名: `replayWebhook`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: POST
   URL: {{ baseUrl.value }}/api/v1/webhooks/replay/
   
   Body:
   {
     "event_id": "{{ webhooksTable.selectedRow.data.event_id }}"
   }
   
   Success event:
     webhookEventsList.trigger()
     utils.showNotification({
       title: '重放成功',
       description: 'Webhook 事件已重新处理',
       notificationType: 'success'
     })
   ```

2. **添加重放按钮**
   - Text: `🔄 重放选中事件`
   - Disabled: 
   ```javascript
   {{
     !webhooksTable.selectedRow ||
     webhooksTable.selectedRow.data.processing_status === 'processed'
   }}
   ```
   - 事件: `onClick` → `replayWebhook.trigger()`

---

## 第 11 章：报表 & 导出（Reports）

### 页面目标
查看各类数据报表，导出数据。

---

### 步骤 11.1：创建报表中心页面

1. **创建新页面**
   - 命名: `Reports`

2. **创建 Tab Container**
   - 拖拽 `Tabs` 组件
   - Tab 1: 概览报表
   - Tab 2: 代理排行榜
   - Tab 3: 佣金对账
   - Tab 4: 异常报告

---

### 步骤 11.2：代理排行榜

1. **新建排行榜查询**
   - 命名: `agentLeaderboard`
   - 配置：
   
   ```javascript
   Resource: POSX API
   Action type: GET
   URL: {{ baseUrl.value }}/api/v1/admin/reports/leaderboard/
   
   Query params:
     period: {{ periodFilter.value }}  // this_month/last_month/this_quarter
     limit: {{ limitInput.value || 20 }}
     site_code: {{ globalSiteCode.value }}
   ```

2. **添加排行榜表格**
   - 显示: rank, agent_email, total_commissions, total_orders, conversion_rate
   - 排序: 按 rank 升序

---

### 步骤 11.3：添加导出功能

1. **添加导出按钮**
   - 对每个表格添加 `Export to CSV` 按钮
   - 配置：
   
   ```javascript
   onClick → utils.exportData({
     data: {{ tableComponent.displayedData }},
     fileName: 'export_{{ moment().format("YYYYMMDD_HHmmss") }}.csv',
     fileType: 'csv'
   })
   ```

---

## 附录 A：API 端点完整清单

### 用户与认证

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| POST | `/api/v1/auth/nonce/` | 获取签名随机数 | Public |
| POST | `/api/v1/auth/wallet/` | 钱包登录 | Public |
| POST | `/api/v1/auth/wallet/bind/` | 绑定钱包 | Authenticated |
| GET | `/api/v1/auth/me/` | 当前用户信息 | Authenticated |

### 站点管理

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| GET | `/api/v1/admin/sites/` | 站点列表 | Admin |
| POST | `/api/v1/admin/sites/` | 创建站点 | Admin |
| GET | `/api/v1/admin/sites/{id}/` | 站点详情 | Admin |
| PUT | `/api/v1/admin/sites/{id}/` | 更新站点 | Admin |
| POST | `/api/v1/admin/sites/{id}/activate/` | 激活/禁用 | Admin |
| GET | `/api/v1/admin/sites/{id}/stats/` | 站点统计 | Admin |
| GET | `/api/v1/admin/sites/assets/` | 链资产列表 | Admin |

### 产品/档位

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| GET | `/api/v1/tiers/` | 产品列表 | Authenticated |
| GET | `/api/v1/tiers/{id}/` | 产品详情 | Authenticated |
| POST | `/api/v1/admin/tiers/` | 创建产品 | Admin |
| PUT | `/api/v1/admin/tiers/{id}/` | 更新产品 | Admin |
| PATCH | `/api/v1/admin/tiers/{id}/` | 部分更新 | Admin |
| POST | `/api/v1/admin/tiers/{id}/adjust-inventory/` | 调整库存 | Admin |
| POST | `/api/v1/admin/tiers/{id}/activate/` | 激活产品 | Admin |
| GET | `/api/v1/admin/tiers/{id}/stats/` | 产品统计 | Admin |

### 订单管理

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| GET | `/api/v1/orders/` | 订单列表 | Authenticated |
| POST | `/api/v1/orders/` | 创建订单 | Authenticated |
| GET | `/api/v1/orders/{id}/` | 订单详情 | Authenticated |
| POST | `/api/v1/orders/preview/` | 订单预览 | Authenticated |
| POST | `/api/v1/orders/promo-codes/validate/` | 验证促销码 | Authenticated |
| GET | `/api/v1/orders/admin/promo-codes/` | 促销码列表 | Admin |
| POST | `/api/v1/orders/admin/promo-codes/` | 创建促销码 | Admin |
| GET | `/api/v1/orders/admin/promo-codes/{id}/usages/` | 使用记录 | Admin |

### 代理管理

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| GET | `/api/v1/agents/` | 代理列表 | Authenticated |
| GET | `/api/v1/agents/dashboard/` | 代理仪表盘 | Authenticated |
| GET | `/api/v1/agents/downlines/` | 下级列表 | Authenticated |
| GET | `/api/v1/agents/balance/` | 余额查询 | Authenticated |
| POST | `/api/v1/agents/withdrawals/` | 申请提现 | Authenticated |
| GET | `/api/v1/agents/withdrawals/` | 提现记录 | Authenticated |
| GET | `/api/v1/agents/statements/` | 佣金报表 | Authenticated |

### 佣金管理

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| GET | `/api/v1/commissions/` | 佣金列表 | Authenticated |
| GET | `/api/v1/commissions/{id}/` | 佣金详情 | Authenticated |
| GET | `/api/v1/commissions/plans/` | 方案列表 | Authenticated |
| POST | `/api/v1/commissions/plans/` | 创建方案 | Admin |

### 分配记录（P1 新增）

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| GET | `/api/v1/allocations/` | 分配列表 | Authenticated |
| GET | `/api/v1/allocations/{id}/` | 分配详情 | Authenticated |
| GET | `/api/v1/allocations/balance/` | 余额统计 | Authenticated |

### Vesting 管理

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| GET | `/api/v1/vesting-releases/` | 释放记录 | Authenticated |
| GET | `/api/v1/admin/vesting/releases/stuck-stats/` | 卡住统计 | Admin |
| POST | `/api/v1/admin/vesting/releases/reconcile/` | 触发对账 | Admin |

### 通知系统（P1 新增）

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| GET | `/api/v1/notifications/` | 通知列表 | Authenticated |
| GET | `/api/v1/notifications/{id}/` | 通知详情 | Authenticated |
| PATCH | `/api/v1/notifications/mark-read/` | 标记已读 | Authenticated |
| GET | `/api/v1/notifications/unread-count/` | 未读统计 | Authenticated |
| GET | `/api/v1/notifications/announcements/` | 公告列表 | Authenticated |

### 系统配置

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| GET | `/api/v1/admin/config/allow-prod-tx/` | 配置状态 | Authenticated |
| GET | `/api/v1/admin/chain-assets/` | 链资产列表 | Authenticated |
| POST | `/api/v1/admin/chain-assets/create/` | 创建资产配置 | Admin |

### Webhook 管理

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| POST | `/api/v1/webhooks/stripe/` | Stripe 回调 | Public (签名验证) |
| POST | `/api/v1/webhooks/fireblocks/` | Fireblocks 回调 | Public (签名验证) |
| POST | `/api/v1/webhooks/replay/` | 重放事件 | Admin |

### 管理员报表

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| GET | `/api/v1/admin/reports/overview/` | 概览报表 | Admin |
| GET | `/api/v1/admin/reports/leaderboard/` | 代理排行榜 | Admin |
| GET | `/api/v1/admin/reports/reconciliation/` | 佣金对账 | Admin |
| GET | `/api/v1/admin/reports/anomalies/` | 异常报告 | Admin |

### 健康检查

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| GET | `/health/` | 简单健康检查 | Public |
| GET | `/ready/` | 详细就绪检查 | Public |
| GET | `/version/` | 版本信息 | Public |

---

## 附录 B：查询模板库（可复制粘贴）

### 模板 1：标准分页查询

```javascript
// 适用于所有列表查询
Resource: POSX API
Action type: GET
URL: {{ baseUrl.value }}/api/v1/<endpoint>/

Query params:
  page: {{ tableComponent.pageIndex + 1 }}
  page_size: {{ tableComponent.pageSize }}
  
Advanced:
  Run on page load: ✓
  Debounce: 300ms
```

### 模板 2：POST 创建资源

```javascript
Resource: POSX API
Action type: POST
URL: {{ baseUrl.value }}/api/v1/<endpoint>/

Body:
{
  // 从表单获取数据
  "field1": "{{ input1.value }}",
  "field2": {{ input2.value }}
}

Success event:
  listQuery.trigger()  // 刷新列表
  formModal.close()    // 关闭表单
  utils.showNotification({
    title: '创建成功',
    notificationType: 'success'
  })

Error event:
  handleApiError.data.handleApiError(error)
```

### 模板 3：PUT/PATCH 更新资源

```javascript
Resource: POSX API
Action type: PUT  // 或 PATCH
URL: {{ baseUrl.value }}/api/v1/<endpoint>/{{ selectedId }}/

Body:
{
  "field1": "{{ editInput1.value }}",
  "field2": {{ editInput2.value }}
}

Success event:
  listQuery.trigger()
  editModal.close()
```

### 模板 4：带筛选的查询

```javascript
Resource: POSX API
Action type: GET
URL: {{ baseUrl.value }}/api/v1/<endpoint>/

Query params:
  page: {{ table.pageIndex + 1 }}
  page_size: 50
  status: {{ statusFilter.value !== 'all' ? statusFilter.value : undefined }}
  date_from: {{ dateFilter.value.start }}
  date_to: {{ dateFilter.value.end }}
  search: {{ searchInput.value || undefined }}

// undefined 参数不会发送到服务器
```

### 模板 5：批量操作

```javascript
Resource: POSX API
Action type: POST
URL: {{ baseUrl.value }}/api/v1/<endpoint>/batch-action/

Body:
{
  "ids": {{ table.selectedRows.map(r => r.id) }},
  "action": "{{ actionType }}"
}

Success event:
  table.clearSelection()
  listQuery.trigger()
```

---

## 附录 C：组件配置示例

### Table 组件标准配置

```javascript
// 基础配置
Data: {{ query.data.results }}
Show search: ✓
Show filters: ✓
Show download: ✓

// 分页
Pagination type: Server-side
Total row count: {{ query.data.count }}
Page size: 50
Page size options: [20, 50, 100]

// 样式
Row height: Compact
Striped rows: ✓
Show border: ✓

// 排序
Sort by: created_at
Sort order: Descending
```

### Modal 组件标准配置

```javascript
// 尺寸
Size: Medium (或 Large)
Full screen: ✗

// 行为
Show on page load: ✗
Close on escape: ✓
Close on overlay click: ✗

// 标题
Title: {{ selectedRow ? '编辑' : '新建' }}

// Footer
Show footer: ✓
Primary button text: {{ selectedRow ? '保存' : '创建' }}
Secondary button text: '取消'
```

### Form 组件标准配置

```javascript
// 布局
Columns: 2
Gap: 16px

// 验证
Show validation: ✓
Validate on: Change

// 提交
Submit button text: '提交'
Reset on submit: ✓
```

---

## 附录 D：权限配置矩阵

### Retool 权限组建议

| 权限组 | 可访问页面 | 说明 |
|--------|----------|------|
| **Super Admin** | 所有页面 | 完全访问权限 |
| **Operations Manager** | Dashboard, Orders, Agents, Commissions, Allocations | 运营管理 |
| **Finance Team** | Dashboard, Commissions, Reports | 财务相关 |
| **Customer Support** | Orders, Users, Notifications | 客户支持 |
| **Viewer** | Dashboard, Reports (只读) | 只读查看 |

### 页面级权限配置

1. **在 Retool 中设置页面权限**
   - 点击页面设置 `⚙️`
   - `Permissions` 标签
   - 选择可访问的权限组

2. **组件级权限**
   - 使用 `Hidden` 或 `Disabled` 属性
   - 示例：
   ```javascript
   // 只有 Admin 可以看到的按钮
   Hidden: {{ !current_user.groups.includes('admin') }}
   ```

---

## 附录 E：故障排查指南

### 问题 1：401 Unauthorized

**症状**: 所有 API 请求返回 401

**原因**:
- JWT Token 过期
- Token 格式错误
- Token 未包含在 Header 中

**解决方案**:
1. 检查 `globalAdminToken` 是否正确设置
2. 重新获取 JWT Token
3. 确认 Resource 配置中的 Bearer Token 设置正确

---

### 问题 2：400 Bad Request - invalid_site

**症状**: 请求返回 `无法识别站点`

**原因**:
- `X-Site-Code` Header 缺失或错误

**解决方案**:
1. 检查 `globalSiteCode` 变量值
2. 确认 Resource 的 Headers 配置包含 `X-Site-Code`
3. 验证站点代码存在于数据库中（NA/ASIA）

---

### 问题 3：查询返回空数据

**症状**: Table 显示 "No data"

**原因**:
- RLS 隔离生效，当前站点无数据
- 筛选条件过于严格
- 用户权限不足

**解决方案**:
1. 切换站点代码（`globalSiteCode`）
2. 放宽筛选条件
3. 检查用户是否有对应权限
4. 查看 Query 的 Response 确认实际返回

---

### 问题 4：数据不刷新

**症状**: 修改数据后列表未更新

**原因**:
- 未配置成功事件触发刷新
- 查询缓存未清除

**解决方案**:
1. 在更新/创建查询的 Success event 中添加：
   ```javascript
   listQuery.trigger()
   ```
2. 手动清除缓存：
   ```javascript
   listQuery.clearCache()
   listQuery.trigger()
   ```

---

### 问题 5：分页显示错误

**症状**: 翻页后数据不正确

**原因**:
- Page index 计算错误（Retool 从 0 开始，API 从 1 开始）
- Total count 未正确设置

**解决方案**:
1. 确认 Query params 中的 page 参数：
   ```javascript
   page: {{ table.pageIndex + 1 }}  // +1 很重要！
   ```
2. 确认 Table 的 Total row count：
   ```javascript
   {{ query.data.count }}
   ```

---

## 附录 F：性能优化建议

### 1. 查询缓存策略

**推荐配置**:
- Dashboard 查询: 缓存 5 分钟
- 列表查询: 缓存 1 分钟
- 详情查询: 不缓存
- 配置查询: 缓存 10 分钟

**设置方法**:
```javascript
Advanced → Cache response
  Time to live: 5 minutes
```

---

### 2. 减少不必要的查询

**优化点**:
1. 使用 `Run trigger: Manual` 避免自动执行
2. 使用 Debounce 减少搜索框触发频率
3. 批量操作合并为单次请求

**示例 - 搜索框优化**:
```javascript
// searchInput 的 onChange 事件
Advanced → Debounce: 500ms
Event → listQuery.trigger()
```

---

### 3. 分页优化

**建议**:
- 默认 page_size: 50（平衡性能和体验）
- 最大 page_size: 100（防止超时）
- 使用 Server-side 分页（不要 Client-side）

---

### 4. 数据展示优化

**大数据量表格**:
- 启用虚拟滚动: `Virtualized rows: ✓`
- 隐藏不常用列
- 使用 tooltip 显示完整内容

**示例**:
```javascript
// 钱包地址列
Display text: {{ currentRow.wallet_address.slice(0,10) }}...
Tooltip: {{ currentRow.wallet_address }}
```

---

### 5. 自动刷新配置

**建议刷新间隔**:
- Dashboard KPI: 5 分钟
- 异常监控: 2 分钟
- 订单列表: 不自动刷新（按需刷新）
- 未读数: 1 分钟

**配置方法**:
```javascript
Advanced → Refresh interval: 5 minutes
```

---

## 附录 G：常用 JavaScript 代码片段

### 1. 格式化货币

```javascript
// 格式化为 USD
function formatUSD(value) {
  return '$' + parseFloat(value || 0).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

// 使用
{{ formatUSD(currentRow.amount_usd) }}
```

### 2. 格式化日期时间

```javascript
// 相对时间
{{ moment(currentRow.created_at).fromNow() }}

// 标准格式
{{ moment(currentRow.created_at).format('YYYY-MM-DD HH:mm:ss') }}

// 仅日期
{{ moment(currentRow.created_at).format('YYYY-MM-DD') }}
```

### 3. 短 UUID 显示

```javascript
// 显示最后 8 位
{{ currentRow.id.slice(-8) }}

// 显示前 8 位
{{ currentRow.id.slice(0, 8) }}

// 显示前后各 4 位
{{ currentRow.id.slice(0, 4) + '...' + currentRow.id.slice(-4) }}
```

### 4. 状态颜色映射

```javascript
// 订单状态
function getOrderStatusColor(status) {
  const colors = {
    'pending': 'orange',
    'paid': 'green',
    'failed': 'red',
    'cancelled': 'gray'
  };
  return colors[status] || 'blue';
}

// 佣金状态
function getCommissionStatusColor(status) {
  const colors = {
    'hold': 'yellow',
    'ready': 'green',
    'paid': 'blue',
    'cancelled': 'gray'
  };
  return colors[status] || 'blue';
}
```

### 5. 批量选择验证

```javascript
// 验证是否选中行
{{ table.selectedRows.length > 0 }}

// 验证选中行状态
{{ table.selectedRows.every(r => r.status === 'ready') }}

// 获取选中 ID 数组
{{ table.selectedRows.map(r => r.id) }}
```

### 6. 条件渲染

```javascript
// 根据状态显示不同内容
{{ 
  currentRow.status === 'pending' ? '⏳ 处理中' :
  currentRow.status === 'completed' ? '✅ 已完成' :
  '❌ 失败'
}}

// 根据数值显示颜色
{{
  currentRow.balance > 10000 ? 'green' :
  currentRow.balance > 1000 ? 'blue' :
  'gray'
}}
```

---

## 附录 H：Retool 最佳实践

### 1. 命名规范

**查询命名**:
- 列表查询: `<resource>List` (例: `ordersList`)
- 详情查询: `<resource>Detail`
- 创建查询: `create<Resource>`
- 更新查询: `update<Resource>`
- 删除查询: `delete<Resource>`

**组件命名**:
- 表格: `<resource>Table`
- 表单: `<resource>Form`
- Modal: `<resource>Modal`
- 筛选器: `<field>Filter`

---

### 2. 错误处理模式

**所有更新操作应包含**:
```javascript
Success event:
  listQuery.trigger()
  modal.close()
  utils.showNotification({ title: '成功', notificationType: 'success' })

Error event:
  handleApiError.data.handleApiError(error)
```

---

### 3. 加载状态处理

**在按钮上显示加载状态**:
```javascript
Loading: {{ query.isFetching }}
Disabled: {{ query.isFetching }}
```

**在表格上显示加载**:
```javascript
Loading: {{ query.isFetching }}
```

---

### 4. 数据验证

**表单提交前验证**:
```javascript
// 在提交按钮的 onClick 前添加验证
if (!form.validate()) {
  utils.showNotification({
    title: '验证失败',
    description: '请检查表单输入',
    notificationType: 'error'
  });
  return;
}

// 继续提交
createQuery.trigger();
```

---

### 5. 全局状态管理

**使用 localStorage 存储偏好**:
```javascript
// 保存站点选择
utils.localStorage.set('selectedSiteCode', siteCodeSelect.value);

// 读取站点选择
{{ utils.localStorage.get('selectedSiteCode') || 'NA' }}
```

---

## 📝 快速检查清单

### 基础设置完成检查

- [ ] Retool 账号已创建并登录
- [ ] POSX API Resource 已配置
- [ ] Bearer Token 认证已设置
- [ ] 全局变量已创建（baseUrl, globalSiteCode, globalAdminToken）
- [ ] 全局 Headers 已配置（X-Site-Code）
- [ ] 错误处理函数已创建
- [ ] 健康检查测试通过

### 10 个核心模块检查

- [ ] 第 1 章: Dashboard 页面已创建（KPI + 异常监控）
- [ ] 第 2 章: Users 页面已创建（用户列表 + 筛选）
- [ ] 第 3 章: Agents 页面已创建（代理管理 + 推荐树 + 余额）
- [ ] 第 4 章: Commissions 页面已创建（佣金列表 + 批量结算）
- [ ] 第 5 章: Tiers 页面已创建（产品配置 + 库存管理）
- [ ] 第 6 章: Sites 页面已创建（站点管理 + 链资产）
- [ ] 第 7 章: Orders 页面已创建（订单列表 + 促销码）
- [ ] 第 8 章: Allocations 页面已创建（分配管理 + Vesting 监控）
- [ ] 第 9 章: Notifications 页面已创建（通知列表 + 公告）
- [ ] 第 10 章: Config 页面已创建（系统配置 + Webhook 重放）

### 功能测试检查

- [ ] 所有列表查询能正常返回数据
- [ ] 分页功能正常工作
- [ ] 筛选器能正确过滤数据
- [ ] 创建/编辑表单能提交成功
- [ ] 批量操作正常工作
- [ ] 导出 CSV 功能正常
- [ ] 错误处理正确显示 Toast
- [ ] 权限控制生效

---

## 🎯 下一步行动

### 完成设置后

1. **数据初始化**
   - 创建测试站点
   - 创建测试用户
   - 创建测试产品
   - 生成测试订单

2. **团队培训**
   - 向运营团队演示各个模块
   - 说明操作流程和注意事项
   - 分配权限组

3. **监控和优化**
   - 观察查询性能
   - 收集用户反馈
   - 优化界面布局
   - 添加更多自动化功能

---

## 📞 技术支持

### 遇到问题时

1. **检查后端健康状态**
   ```bash
   curl http://localhost:8000/ready/
   ```

2. **查看后端日志**
   ```bash
   docker-compose logs -f backend
   ```

3. **检查 Retool Query 响应**
   - 点击查询 → `Results` 标签
   - 查看 Status Code 和 Response Body

4. **联系开发团队**
   - 提供: 页面名称、查询名称、错误信息、截图

---

## ✅ 设置完成

恭喜！您已经完成 POSX Framework Retool 运营后台的完整设置。

### 系统功能

- ✅ 10 个核心运营模块
- ✅ 60+ API 端点对接
- ✅ 完整的权限控制
- ✅ 统一的错误处理
- ✅ 实时数据监控

### 立即开始使用

现在您可以：
- 查看实时业务数据
- 管理用户和代理
- 处理订单和佣金
- 监控代币分配
- 发布系统通知
- 导出数据报表

---

**手册版本**: v1.0  
**最后更新**: 2025-11-11  
**维护团队**: POSX Framework Team  
**反馈渠道**: support@posx.com

**祝您使用愉快！** 🎉


# Backend Scripts - POSX Framework

## 📋 概述

本目录包含 POSX 后端的所有环境验证、诊断工具和初始化脚本。

**注意**: 这些是工具脚本，不是自动化测试。自动化测试请查看 `backend/tests/` 和 `backend/apps/*/tests/`。

---

## 📁 脚本分类

### 🔍 环境验证脚本

| 脚本 | 用途 | 使用时机 |
|------|------|---------|
| `check_env.py` | 完整环境变量检查（依赖Django环境） | 启动前 |
| `check_env_simple.py` | 简单环境变量检查（不依赖Django） | 配置后立即验证 |
| `check_env_loading.py` | 测试环境变量加载逻辑 | 调试配置问题 |
| `check_db_schema.py` | 数据库schema验证 | 迁移后 |
| `check_auth0_setup.py` | Auth0配置检查 | Auth0配置后 |
| `verify_setup.py` | 综合setup验证 | 完整配置后 |

**使用示例**:
```bash
# 快速检查（无需Django环境）
python backend/scripts/check_env_simple.py

# 完整检查（需要Django环境）
cd backend
python scripts/check_env.py

# 数据库检查
python scripts/check_db_schema.py
```

---

### 🔧 诊断工具脚本

| 脚本 | 用途 | 使用场景 |
|------|------|---------|
| `diagnose_issuer.py` | 诊断Auth0 Issuer配置问题 | JWT验证失败时 |

**使用示例**:
```bash
cd backend
python scripts/diagnose_issuer.py
```

---

### 🛠️ 初始化工具脚本

| 脚本 | 用途 | 使用时机 |
|------|------|---------|
| `create_test_sites.py` | 创建测试站点数据 | 数据库初始化 |

**使用示例**:
```bash
cd backend
python scripts/create_test_sites.py
```

---

### 🧪 Phase 测试脚本

| 脚本 | 用途 | 使用时机 |
|------|------|---------|
| `phase_tests/phase_c_acceptance.sh` | Phase C 验收测试自动化脚本 | Phase C 交付前 |

**使用示例**:
```bash
cd backend
bash scripts/phase_tests/phase_c_acceptance.sh
```

---

## 🎯 快速参考

### 新环境配置流程

```bash
# 1. 简单检查
python backend/scripts/check_env_simple.py

# 2. 完整检查（需先安装依赖）
cd backend
pip install -r requirements/production.txt
python scripts/check_env.py

# 3. 数据库检查
python scripts/check_db_schema.py

# 4. 综合验证
python scripts/verify_setup.py
```

### 问题诊断流程

```bash
# Auth0 问题
python backend/scripts/diagnose_issuer.py

# 环境变量问题
python backend/scripts/check_env_loading.py

# 数据库问题
python backend/scripts/check_db_schema.py
```

---

## 📝 与测试的区别

| 类型 | 位置 | 运行方式 | 目的 |
|------|------|---------|------|
| **工具脚本** | `backend/scripts/` | 手动执行 | 环境验证、诊断、初始化 |
| **集成测试** | `backend/tests/` | `pytest backend/tests/` | 自动化功能测试 |
| **单元测试** | `apps/*/tests/` | `pytest apps/` | 模块级单元测试 |

---

## 🔄 添加新脚本

### 命名规范

- 检查脚本：`check_<target>.py`
- 验证脚本：`verify_<target>.py`
- 诊断脚本：`diagnose_<target>.py`
- 创建/生成：`create_<target>.py` 或 `generate_<target>.py`

### 示例模板

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
脚本说明

使用方法：
    python scripts/<script_name>.py [options]
"""
import sys
from pathlib import Path

def main():
    """主函数"""
    # 脚本逻辑
    pass

if __name__ == '__main__':
    sys.exit(main())
```

---

## 📞 联系

如有问题，请查看：
- 主README: `../README.md`
- 文档索引: `../docs/00_README.md`
- 测试说明: `../tests/__init__.py`


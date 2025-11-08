---
name: Documentation Pull Request
about: Submit documentation changes
title: '[docs] '
labels: documentation
assignees: ''

---

## 📝 变更说明

<!-- 简要描述本次文档变更的内容 -->

## 📋 检查清单

请确认以下所有项目：

### 文档质量
- [ ] 使用了正确的命名前缀（PHASE_, CONFIG_, SETUP_, SPEC_, REPORT_, CHECKLIST_, QUICK_）
- [ ] 文件已放入正确的目录（config/, phases/, specs/, reports/, startup/）
- [ ] 如果是新文档，已使用 `docs/templates/` 中的模板
- [ ] 代码块已指定语言（```python, ```bash 等）
- [ ] 链接使用相对路径且正确

### 索引更新
- [ ] 如果添加了新文档，已更新 `docs/00_README.md` 索引
- [ ] 索引链接路径正确
- [ ] 索引分类合理

### 自动化检查
- [ ] 已本地运行 `python scripts/check_md_naming.py` 且通过
- [ ] 文档中无明显拼写错误
- [ ] 格式化正确（标题、列表、代码块等）

### PR 规范
- [ ] PR 标题以 `[docs]` 开头
- [ ] 已添加 `documentation` 标签

## 📎 相关链接

<!-- 如果相关，请链接相关的Issue或PR -->

## 🔍 截图（如适用）

<!-- 如果有UI变更或新增图表，请添加截图 -->

---

**提醒**: 提交后会自动运行文档质量检查，请确保所有检查通过。


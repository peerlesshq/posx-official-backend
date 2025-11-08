#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
POSX 文档命名规范检查脚本

检查 docs/ 目录下的 Markdown 文件是否符合命名规范。

命名规范：
- 必须使用以下前缀之一：PHASE_, CONFIG_, SETUP_, SPEC_, REPORT_, CHECKLIST_, QUICK_, ENV_
- 使用大写字母和下划线分隔
- misc/UNSORTED/ 目录允许任意命名但会打印警告

退出码：
- 0: 所有文件符合规范
- 1: 存在不符合规范的文件
"""

import re
import sys
from pathlib import Path

# 允许的文件名前缀（正则表达式）
VALID_PREFIX_PATTERN = re.compile(
    r'^(PHASE|CONFIG|SETUP|SPEC|REPORT|CHECKLIST|QUICK|ENV)_.*\.md$',
    re.IGNORECASE
)

# 特殊允许的文件名
ALLOWED_SPECIAL = {
    '00_README.md',
    'CHANGELOG.md',
    'AI_CONTEXT.md',
    'DEVELOPMENT.md',
    'ARCHITECTURE.md',
}

def check_filename(file_path):
    """
    检查文件名是否符合规范
    
    Returns:
        tuple: (is_valid, message)
    """
    filename = file_path.name
    parent_dir = file_path.parent.name
    
    # 特殊允许的文件名
    if filename in ALLOWED_SPECIAL:
        return True, f"[OK] {file_path.relative_to('docs')}: Special allowed"
    
    # UNSORTED 目录允许任意命名但警告
    if 'UNSORTED' in file_path.parts:
        return True, f"[WARN] {file_path.relative_to('docs')}: UNSORTED (needs filing)"
    
    # 检查是否匹配规范前缀
    if VALID_PREFIX_PATTERN.match(filename):
        return True, f"[OK] {file_path.relative_to('docs')}: Valid"
    
    # 不符合规范
    return False, f"[FAIL] {file_path.relative_to('docs')}: Invalid naming"

def main():
    """主函数"""
    print("="*60)
    print("POSX 文档命名规范检查")
    print("="*60)
    print()
    
    docs_dir = Path('docs')
    if not docs_dir.exists():
        print("错误: docs/ 目录不存在")
        return 1
    
    # 收集所有 .md 文件
    md_files = list(docs_dir.rglob('*.md'))
    
    if not md_files:
        print("警告: 未找到任何 Markdown 文件")
        return 0
    
    valid_count = 0
    warning_count = 0
    invalid_count = 0
    invalid_files = []
    
    for md_file in sorted(md_files):
        is_valid, message = check_filename(md_file)
        
        if '[WARN]' in message:
            warning_count += 1
            print(message)
        elif is_valid:
            valid_count += 1
            print(message)
        else:
            invalid_count += 1
            invalid_files.append(md_file.relative_to('docs'))
            print(message)
    
    # 打印汇总
    print()
    print("="*60)
    print(f"Summary:")
    print(f"  [OK] Valid: {valid_count} files")
    print(f"  [WARN] Needs filing: {warning_count} files")
    print(f"  [FAIL] Invalid: {invalid_count} files")
    print("="*60)
    
    if invalid_count > 0:
        print()
        print("Invalid files:")
        for f in invalid_files:
            print(f"  - {f}")
        print()
        print("Please rename using one of these prefixes:")
        print("  PHASE_, CONFIG_, SETUP_, SPEC_, REPORT_, CHECKLIST_, QUICK_, ENV_")
        print()
        return 1
    
    if warning_count > 0:
        print()
        print(f"Note: {warning_count} files in UNSORTED/ directory need proper filing")
    
    print()
    print("All files passed naming check!")
    return 0

if __name__ == '__main__':
    sys.exit(main())


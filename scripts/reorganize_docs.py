#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
POSX 文档重构脚本
按照规范移动和重命名 Markdown 文件
"""
import os
import shutil
from pathlib import Path

# 文件映射表：(当前路径, 新路径)
FILE_MAPPINGS = [
    # Startup 文档
    ("QUICKSTART.md", "docs/startup/QUICK_STARTUP.md"),
    ("QUICK_ENV_SETUP.md", "docs/startup/QUICK_ENV_SETUP.md"),
    ("STARTUP_AND_TEST_GUIDE.md", "docs/startup/STARTUP_AND_TEST_GUIDE.md"),
    ("NEXT_STEPS.md", "docs/startup/QUICK_NEXT_STEPS.md"),
    
    # Config 文档
    ("CONFIG_COMPLETE.md", "docs/config/CONFIG_ENVIRONMENT.md"),
    ("COMPLETE_ENV_SETUP.md", "docs/config/CONFIG_ENV_SETUP.md"),
    ("ENV_VARIABLES.md", "docs/config/CONFIG_ENV_VARIABLES.md"),
    ("ENV_VARIABLES_PHASE_C.md", "docs/config/CONFIG_ENV_PHASE_C.md"),
    ("ENVIRONMENT_SETUP_GUIDE.md", "docs/config/SETUP_ENVIRONMENT.md"),
    ("YOUR_ENV_CONFIG.md", "docs/config/CONFIG_ENV_CUSTOM.md"),
    ("AUTH0_CONFIG.md", "docs/config/CONFIG_AUTH0.md"),
    ("STRIPE_CLI_SETUP.md", "docs/config/SETUP_STRIPE_CLI.md"),
    ("STRIPE_CONFIG_COMPLETE.md", "docs/config/CONFIG_STRIPE.md"),
    
    # Phase C 文档
    ("PHASE_C_ACCEPTANCE.md", "docs/phases/PHASE_C_ACCEPTANCE.md"),
    ("PHASE_C_IMPLEMENTATION.md", "docs/phases/PHASE_C_IMPLEMENTATION.md"),
    ("PHASE_C_FILES_CHECKLIST.md", "docs/phases/PHASE_C_FILES_CHECKLIST.md"),
    ("PHASE_C_DELIVERY.md", "docs/phases/PHASE_C_DELIVERY.md"),
    ("PHASE_C_FINAL_SUMMARY.md", "docs/phases/PHASE_C_FINAL_SUMMARY.md"),
    ("backend/PHASE_C_PLAN.md", "docs/phases/PHASE_C_PLAN.md"),
    ("backend/PHASE_C_QUICKSTART.md", "docs/phases/PHASE_C_QUICKSTART.md"),
    ("backend/PHASE_B_IMPROVEMENTS_CHECKLIST.md", "docs/phases/PHASE_B_IMPROVEMENTS_CHECKLIST.md"),
    
    # Reports / Checklists
    ("ENV_FINAL_CHECKLIST.md", "docs/reports/CHECKLIST_ENV_FINAL.md"),
    ("P0_P1_CHECKLIST.md", "docs/reports/CHECKLIST_P0_P1.md"),
    ("PRODUCTION_CHECKLIST.md", "docs/reports/CHECKLIST_PRODUCTION.md"),
    ("00_DELIVERY_CHECKLIST.md", "docs/reports/CHECKLIST_DELIVERY.md"),
    ("ACCEPTANCE_TESTING.md", "docs/reports/REPORT_ACCEPTANCE_TESTING.md"),
    ("FINAL_SUMMARY.md", "docs/reports/REPORT_FINAL_SUMMARY.md"),
    ("RELEASE_SUMMARY.md", "docs/reports/REPORT_RELEASE_SUMMARY.md"),
    ("DELIVERY_SUMMARY.md", "docs/reports/REPORT_DELIVERY_SUMMARY.md"),
    ("IMPLEMENTATION_SUMMARY.md", "docs/reports/REPORT_IMPLEMENTATION_SUMMARY.md"),
    ("VERIFICATION_REPORT.md", "docs/reports/REPORT_VERIFICATION.md"),
    ("AUTH0_FINAL_STATUS.md", "docs/reports/REPORT_AUTH0_STATUS.md"),
    ("AUTH0_TEST_SUMMARY.md", "docs/reports/REPORT_AUTH0_TEST.md"),
    ("AUTH0_TESTING_GUIDE.md", "docs/reports/REPORT_AUTH0_TESTING.md"),
    ("INIT_STATUS.md", "docs/reports/REPORT_INIT_STATUS.md"),
    ("INIT_COMPLETE.md", "docs/reports/REPORT_INIT_COMPLETE.md"),
    ("POSX_Technical_Corrections.md", "docs/reports/REPORT_TECHNICAL_CORRECTIONS.md"),
    ("POSX_Review_Analysis.md", "docs/reports/REPORT_REVIEW_ANALYSIS.md"),
    ("CHANGELOG.md", "docs/reports/CHANGELOG.md"),
    ("backend/IMPROVEMENTS_SUMMARY.md", "docs/reports/REPORT_IMPROVEMENTS_SUMMARY.md"),
    ("backend/QUICKSTART_IMPROVEMENTS.md", "docs/reports/REPORT_QUICKSTART_IMPROVEMENTS.md"),
    
    # Specs
    ("POSX_System_Specification_v1.0.0.md", "docs/specs/SPEC_SYSTEM_ARCH_v1.0.0.md"),
    ("POSX_System_Specification_v1_0_0.md", "docs/specs/SPEC_SYSTEM_ARCH_v1_0_0_ALT.md"),
    ("POSX_System_Specification_v1_0_4_RLS_Production.md", "docs/specs/SPEC_RLS_POLICY_v1.0.4.md"),
    ("POSX_Framework_Guide.md", "docs/specs/SPEC_FRAMEWORK_GUIDE.md"),
    ("POSX_Framework_v3_README.md", "docs/specs/SPEC_FRAMEWORK_v3.md"),
    
    # Misc/UNSORTED（无法自动判断的）
    ("DOWNLOAD_README.md", "docs/misc/UNSORTED/DOWNLOAD_README.md"),
    
    # 已存在的 docs/ 文件（保持但可能重命名）
    ("docs/AI_CONTEXT.md", "docs/misc/AI_CONTEXT.md"),
    ("docs/ARCHITECTURE.md", "docs/specs/SPEC_ARCHITECTURE.md"),
    ("docs/DEVELOPMENT.md", "docs/misc/DEVELOPMENT.md"),
    
    # backend/ENV_SETUP_WIZARD.md 移到 config
    ("backend/ENV_SETUP_WIZARD.md", "docs/config/SETUP_ENV_WIZARD.md"),
]

def move_file(src, dst):
    """移动文件，如果源文件存在"""
    src_path = Path(src)
    if not src_path.exists():
        print(f"  [SKIP] {src} (不存在)")
        return False
    
    dst_path = Path(dst)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 使用 git mv 以保持历史
    try:
        os.system(f'git mv "{src}" "{dst}"')
        print(f"  [MOVE] {src} → {dst}")
        return True
    except Exception as e:
        print(f"  [ERROR] {src}: {e}")
        return False

def main():
    print("="*60)
    print("POSX 文档重构")
    print("="*60)
    print()
    
    moved_count = 0
    skipped_count = 0
    
    for src, dst in FILE_MAPPINGS:
        if move_file(src, dst):
            moved_count += 1
        else:
            skipped_count += 1
    
    print()
    print("="*60)
    print(f"完成: {moved_count} 个文件已移动, {skipped_count} 个文件跳过")
    print("="*60)

if __name__ == "__main__":
    main()


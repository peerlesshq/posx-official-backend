"""
Create initial schema
注意：这是一个简化的占位迁移
实际生产中需要包含完整的表结构
"""
from django.db import migrations


class Migration(migrations.Migration):
    """
    创建初始数据库架构
    """
    
    dependencies = [
        ('core', '0001_initial'),
    ]
    
    operations = [
        migrations.RunSQL(
            sql="""
                -- ============================================
                -- 基础表结构（简化版）
                -- 实际生产需要完整的表定义
                -- ============================================
                
                -- 提示: 这里应该包含所有表的 CREATE TABLE 语句
                -- 参考 POSX_System_Specification 文档中的数据模型
                
                SELECT 1;  -- 占位语句
            """,
            reverse_sql="-- 回滚 SQL"
        ),
    ]

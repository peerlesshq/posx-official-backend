# Generated manually for Promo Code RLS

from django.db import migrations


class Migration(migrations.Migration):
    """
    为 Promo Code 表启用 RLS (Row Level Security)
    
    ⚠️ 重要：
    - 确保多站点数据隔离
    - Admin 角色可以查看所有站点数据（使用 admin 连接）
    - 普通用户只能访问自己站点的数据
    """

    dependencies = [
        ('orders', '0006_add_promo_codes'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- ========== PromoCode 表 RLS ==========
                
                -- 1. 启用 RLS（强制执行）
                ALTER TABLE promo_codes ENABLE ROW LEVEL SECURITY;
                ALTER TABLE promo_codes FORCE ROW LEVEL SECURITY;
                
                -- 2. 创建策略：站点隔离（普通用户）
                CREATE POLICY rls_promo_codes_site_isolation ON promo_codes
                    FOR ALL
                    USING (site_id = current_setting('app.current_site_id', true)::uuid)
                    WITH CHECK (site_id = current_setting('app.current_site_id', true)::uuid);
                
                -- 3. 创建策略：Admin 只读（使用 admin 连接）
                CREATE POLICY rls_promo_codes_admin_read ON promo_codes
                    FOR SELECT
                    USING (current_user = 'posx_admin');
                
                
                -- ========== PromoCodeUsage 表 RLS ==========
                
                -- 1. 启用 RLS（强制执行）
                ALTER TABLE promo_code_usages ENABLE ROW LEVEL SECURITY;
                ALTER TABLE promo_code_usages FORCE ROW LEVEL SECURITY;
                
                -- 2. 创建策略：通过 order 关联站点隔离
                -- 注意：PromoCodeUsage 没有直接的 site_id，通过 order 间接关联
                CREATE POLICY rls_promo_code_usages_site_isolation ON promo_code_usages
                    FOR ALL
                    USING (
                        order_id IN (
                            SELECT order_id FROM orders 
                            WHERE site_id = current_setting('app.current_site_id', true)::uuid
                        )
                    )
                    WITH CHECK (
                        order_id IN (
                            SELECT order_id FROM orders 
                            WHERE site_id = current_setting('app.current_site_id', true)::uuid
                        )
                    );
                
                -- 3. 创建策略：Admin 只读
                CREATE POLICY rls_promo_code_usages_admin_read ON promo_code_usages
                    FOR SELECT
                    USING (current_user = 'posx_admin');
            """,
            reverse_sql="""
                -- 回滚：禁用 RLS 并删除策略
                
                -- PromoCodeUsage
                DROP POLICY IF EXISTS rls_promo_code_usages_admin_read ON promo_code_usages;
                DROP POLICY IF EXISTS rls_promo_code_usages_site_isolation ON promo_code_usages;
                ALTER TABLE promo_code_usages DISABLE ROW LEVEL SECURITY;
                
                -- PromoCode
                DROP POLICY IF EXISTS rls_promo_codes_admin_read ON promo_codes;
                DROP POLICY IF EXISTS rls_promo_codes_site_isolation ON promo_codes;
                ALTER TABLE promo_codes DISABLE ROW LEVEL SECURITY;
            """
        ),
    ]


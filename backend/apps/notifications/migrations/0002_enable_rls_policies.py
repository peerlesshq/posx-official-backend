# POSX Notifications RLS Migration
# ⭐ 核心检查点: Row Level Security (RLS) 策略

from django.db import migrations


class Migration(migrations.Migration):
    """
    启用 RLS 策略
    
    ⭐ 关键要求:
    1. FORCE ROW LEVEL SECURITY - 即使超级用户也受限
    2. UUID 类型转换 - ::uuid 确保类型安全
    3. Admin 只读策略 - posx_admin 可跨站查询
    4. 完整的 reverse_sql - 支持回滚
    """

    dependencies = [
        ('notifications', '0001_initial'),
        ('core', '0004_enable_rls_policies'),  # 依赖 core RLS 已启用
    ]

    operations = [
        # ============================================
        # 1. notification_templates 表 RLS
        # ============================================
        migrations.RunSQL(
            sql="""
                -- 启用 RLS（FORCE 模式）
                ALTER TABLE notification_templates ENABLE ROW LEVEL SECURITY;
                ALTER TABLE notification_templates FORCE ROW LEVEL SECURITY;
                
                -- 策略1：站点隔离（应用用户）
                -- 全局模板（site_id IS NULL）或当前站点模板可见
                CREATE POLICY rls_notification_templates_site_isolation ON notification_templates
                    FOR ALL
                    USING (
                        site_id IS NULL OR 
                        site_id = current_setting('app.current_site_id', true)::uuid
                    )
                    WITH CHECK (
                        site_id IS NULL OR 
                        site_id = current_setting('app.current_site_id', true)::uuid
                    );
                
                -- 策略2：管理员只读（跨站查询）
                CREATE POLICY rls_notification_templates_admin_readonly ON notification_templates
                    FOR SELECT TO posx_admin
                    USING (true);
            """,
            reverse_sql="""
                -- 回滚：禁用 RLS
                DROP POLICY IF EXISTS rls_notification_templates_admin_readonly ON notification_templates;
                DROP POLICY IF EXISTS rls_notification_templates_site_isolation ON notification_templates;
                ALTER TABLE notification_templates DISABLE ROW LEVEL SECURITY;
            """
        ),
        
        # ============================================
        # 2. notifications 表 RLS
        # ============================================
        migrations.RunSQL(
            sql="""
                -- 启用 RLS（FORCE 模式）
                ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
                ALTER TABLE notifications FORCE ROW LEVEL SECURITY;
                
                -- 策略1：站点隔离（应用用户）
                -- ⭐ 注意：recipient_id 由应用层过滤，RLS 只负责 site_id 隔离
                CREATE POLICY rls_notifications_site_isolation ON notifications
                    FOR ALL
                    USING (site_id = current_setting('app.current_site_id', true)::uuid)
                    WITH CHECK (site_id = current_setting('app.current_site_id', true)::uuid);
                
                -- 策略2：管理员只读（跨站查询）
                CREATE POLICY rls_notifications_admin_readonly ON notifications
                    FOR SELECT TO posx_admin
                    USING (true);
            """,
            reverse_sql="""
                DROP POLICY IF EXISTS rls_notifications_admin_readonly ON notifications;
                DROP POLICY IF EXISTS rls_notifications_site_isolation ON notifications;
                ALTER TABLE notifications DISABLE ROW LEVEL SECURITY;
            """
        ),
        
        # ============================================
        # 3. notification_channel_tasks 表 RLS
        # ============================================
        migrations.RunSQL(
            sql="""
                -- 启用 RLS（FORCE 模式）
                ALTER TABLE notification_channel_tasks ENABLE ROW LEVEL SECURITY;
                ALTER TABLE notification_channel_tasks FORCE ROW LEVEL SECURITY;
                
                -- 策略1：站点隔离（通过 notification 关联）
                CREATE POLICY rls_notification_channel_tasks_site_isolation ON notification_channel_tasks
                    FOR ALL
                    USING (
                        EXISTS (
                            SELECT 1 FROM notifications n
                            WHERE n.notification_id = notification_channel_tasks.notification_id
                            AND n.site_id = current_setting('app.current_site_id', true)::uuid
                        )
                    );
                
                -- 策略2：管理员只读（跨站查询）
                CREATE POLICY rls_notification_channel_tasks_admin_readonly ON notification_channel_tasks
                    FOR SELECT TO posx_admin
                    USING (true);
            """,
            reverse_sql="""
                DROP POLICY IF EXISTS rls_notification_channel_tasks_admin_readonly ON notification_channel_tasks;
                DROP POLICY IF EXISTS rls_notification_channel_tasks_site_isolation ON notification_channel_tasks;
                ALTER TABLE notification_channel_tasks DISABLE ROW LEVEL SECURITY;
            """
        ),
        
        # ============================================
        # 4. notification_preferences 表 RLS
        # ============================================
        migrations.RunSQL(
            sql="""
                -- 启用 RLS（FORCE 模式）
                ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;
                ALTER TABLE notification_preferences FORCE ROW LEVEL SECURITY;
                
                -- 策略1：站点隔离（应用用户）
                CREATE POLICY rls_notification_preferences_site_isolation ON notification_preferences
                    FOR ALL
                    USING (site_id = current_setting('app.current_site_id', true)::uuid)
                    WITH CHECK (site_id = current_setting('app.current_site_id', true)::uuid);
                
                -- 策略2：管理员只读（跨站查询）
                CREATE POLICY rls_notification_preferences_admin_readonly ON notification_preferences
                    FOR SELECT TO posx_admin
                    USING (true);
            """,
            reverse_sql="""
                DROP POLICY IF EXISTS rls_notification_preferences_admin_readonly ON notification_preferences;
                DROP POLICY IF EXISTS rls_notification_preferences_site_isolation ON notification_preferences;
                ALTER TABLE notification_preferences DISABLE ROW LEVEL SECURITY;
            """
        ),
        
        # ============================================
        # 5. notification_read_receipts 表 RLS
        # ============================================
        migrations.RunSQL(
            sql="""
                -- 启用 RLS（FORCE 模式）
                ALTER TABLE notification_read_receipts ENABLE ROW LEVEL SECURITY;
                ALTER TABLE notification_read_receipts FORCE ROW LEVEL SECURITY;
                
                -- 策略1：站点隔离（通过 notification 关联）
                CREATE POLICY rls_notification_read_receipts_site_isolation ON notification_read_receipts
                    FOR ALL
                    USING (
                        EXISTS (
                            SELECT 1 FROM notifications n
                            WHERE n.notification_id = notification_read_receipts.notification_id
                            AND n.site_id = current_setting('app.current_site_id', true)::uuid
                        )
                    );
                
                -- 策略2：管理员只读（跨站查询）
                CREATE POLICY rls_notification_read_receipts_admin_readonly ON notification_read_receipts
                    FOR SELECT TO posx_admin
                    USING (true);
            """,
            reverse_sql="""
                DROP POLICY IF EXISTS rls_notification_read_receipts_admin_readonly ON notification_read_receipts;
                DROP POLICY IF EXISTS rls_notification_read_receipts_site_isolation ON notification_read_receipts;
                ALTER TABLE notification_read_receipts DISABLE ROW LEVEL SECURITY;
            """
        ),
        
        # ============================================
        # 6. 验证 RLS 状态
        # ============================================
        migrations.RunSQL(
            sql="""
                DO $$
                DECLARE
                    rls_tables TEXT[] := ARRAY[
                        'notification_templates',
                        'notifications',
                        'notification_channel_tasks',
                        'notification_preferences',
                        'notification_read_receipts'
                    ];
                    tbl TEXT;
                    rls_status BOOLEAN;
                BEGIN
                    FOREACH tbl IN ARRAY rls_tables LOOP
                        SELECT rowsecurity INTO rls_status
                        FROM pg_tables
                        WHERE tablename = tbl;
                        
                        IF NOT rls_status THEN
                            RAISE EXCEPTION 'RLS not enabled on table: %', tbl;
                        END IF;
                        
                        RAISE NOTICE 'RLS verified on: %', tbl;
                    END LOOP;
                    
                    RAISE NOTICE 'All notification tables have RLS enabled ✓';
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
    ]


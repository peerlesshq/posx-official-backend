"""
订单佣金快照初始迁移

⭐ RLS 安全：
- 通过 order_id 关联 orders 表
- 订单受 RLS 保护，快照自动继承隔离
- 显式启用 RLS 以确保安全
"""
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('orders', '0001_initial'),  # 依赖 orders 表
    ]

    operations = [
        # ========================================
        # 创建 order_commission_policy_snapshots 表
        # ========================================
        migrations.CreateModel(
            name='OrderCommissionPolicySnapshot',
            fields=[
                ('snapshot_id', models.UUIDField(
                    primary_key=True,
                    default=uuid.uuid4,
                    editable=False,
                    help_text='快照唯一标识'
                )),
                ('order_id', models.UUIDField(
                    unique=True,
                    db_index=True,
                    help_text='关联订单ID（OneToOne）'
                )),
                ('plan_id', models.UUIDField(
                    help_text='佣金计划ID（快照时）'
                )),
                ('plan_name', models.CharField(
                    max_length=100,
                    help_text='计划名称'
                )),
                ('plan_version', models.PositiveIntegerField(
                    help_text='计划版本'
                )),
                ('plan_mode', models.CharField(
                    max_length=20,
                    help_text='计算模式'
                )),
                ('diff_reward_enabled', models.BooleanField(
                    default=False,
                    help_text='是否启用差额奖励'
                )),
                ('tiers_json', models.JSONField(
                    help_text='层级配置（JSONB 格式）'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'order_commission_policy_snapshots',
                'verbose_name': 'Order Commission Policy Snapshot',
                'verbose_name_plural': 'Order Commission Policy Snapshots',
            },
        ),
        
        # ========================================
        # 索引
        # ========================================
        migrations.AddIndex(
            model_name='ordercommissionpolicysnapshot',
            index=models.Index(
                fields=['order_id'],
                name='ocps_order_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='ordercommissionpolicysnapshot',
            index=models.Index(
                fields=['plan_id'],
                name='ocps_plan_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='ordercommissionpolicysnapshot',
            index=models.Index(
                fields=['created_at'],
                name='ocps_created_idx'
            ),
        ),
        
        # ========================================
        # RLS 策略 ⭐
        # ========================================
        migrations.RunSQL(
            sql="""
                -- 启用 RLS
                ALTER TABLE order_commission_policy_snapshots ENABLE ROW LEVEL SECURITY;
                ALTER TABLE order_commission_policy_snapshots FORCE ROW LEVEL SECURITY;
                
                -- RLS 策略：通过 order 关联隔离
                CREATE POLICY rls_order_snapshots_isolation ON order_commission_policy_snapshots
                    FOR ALL
                    USING (
                        EXISTS (
                            SELECT 1 FROM orders
                            WHERE orders.order_id = order_commission_policy_snapshots.order_id
                            AND orders.site_id = current_setting('app.current_site_id', true)::uuid
                        )
                    )
                    WITH CHECK (
                        EXISTS (
                            SELECT 1 FROM orders
                            WHERE orders.order_id = order_commission_policy_snapshots.order_id
                            AND orders.site_id = current_setting('app.current_site_id', true)::uuid
                        )
                    );
                
                -- Admin 只读策略
                CREATE POLICY rls_order_snapshots_admin_read ON order_commission_policy_snapshots
                    FOR SELECT
                    USING (pg_has_role(current_user, 'posx_admin', 'member'));
            """,
            reverse_sql="""
                -- 回滚 RLS
                ALTER TABLE order_commission_policy_snapshots DISABLE ROW LEVEL SECURITY;
            """
        ),
    ]



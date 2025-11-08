"""
代理应用初始迁移

⭐ RLS 安全：
- agent_trees 表启用 RLS（site_id 隔离）
- agent_stats 表启用 RLS（site_id 隔离）
"""
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        # ========================================
        # 创建 agent_trees 表
        # ========================================
        migrations.CreateModel(
            name='AgentTree',
            fields=[
                ('tree_id', models.UUIDField(
                    primary_key=True,
                    default=uuid.uuid4,
                    editable=False,
                    help_text='关系唯一标识'
                )),
                ('site_id', models.UUIDField(
                    db_index=True,
                    help_text='站点ID（RLS隔离）'
                )),
                ('agent', models.UUIDField(
                    db_index=True,
                    help_text='代理用户ID'
                )),
                ('parent', models.UUIDField(
                    null=True,
                    blank=True,
                    db_index=True,
                    help_text='上级代理ID（NULL=根节点）'
                )),
                ('depth', models.PositiveSmallIntegerField(
                    default=1,
                    help_text='深度（1=直接推荐）'
                )),
                ('path', models.TextField(
                    help_text='路径（/root/parent/agent/）'
                )),
                ('active', models.BooleanField(
                    default=True,
                    db_index=True,
                    help_text='激活状态'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'agent_trees',
                'verbose_name': 'Agent Tree',
                'verbose_name_plural': 'Agent Trees',
            },
        ),
        
        # ========================================
        # 创建 agent_stats 表
        # ========================================
        migrations.CreateModel(
            name='AgentStats',
            fields=[
                ('stat_id', models.UUIDField(
                    primary_key=True,
                    default=uuid.uuid4,
                    editable=False,
                    help_text='统计记录ID'
                )),
                ('site_id', models.UUIDField(
                    db_index=True,
                    help_text='站点ID（RLS隔离）'
                )),
                ('agent', models.UUIDField(
                    unique=True,
                    db_index=True,
                    help_text='代理用户ID'
                )),
                ('total_customers', models.PositiveIntegerField(
                    default=0,
                    help_text='累计客户数'
                )),
                ('direct_customers', models.PositiveIntegerField(
                    default=0,
                    help_text='直接客户数（depth=1）'
                )),
                ('total_sales', models.DecimalField(
                    max_digits=18,
                    decimal_places=6,
                    default=0,
                    help_text='累计销售额（USD）'
                )),
                ('total_commissions', models.DecimalField(
                    max_digits=18,
                    decimal_places=6,
                    default=0,
                    help_text='累计佣金'
                )),
                ('last_order_at', models.DateTimeField(
                    null=True,
                    blank=True,
                    help_text='最后订单时间'
                )),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'agent_stats',
                'verbose_name': 'Agent Stats',
                'verbose_name_plural': 'Agent Stats',
            },
        ),
        
        # ========================================
        # 索引
        # ========================================
        migrations.AddIndex(
            model_name='agenttree',
            index=models.Index(
                fields=['site_id', 'agent'],
                name='at_site_agent_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='agenttree',
            index=models.Index(
                fields=['site_id', 'parent'],
                name='at_site_parent_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='agenttree',
            index=models.Index(
                fields=['site_id', 'active'],
                name='at_site_active_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='agenttree',
            index=models.Index(
                fields=['depth'],
                name='at_depth_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='agenttree',
            index=models.Index(
                fields=['created_at'],
                name='at_created_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='agentstats',
            index=models.Index(
                fields=['site_id', 'agent'],
                name='as_site_agent_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='agentstats',
            index=models.Index(
                fields=['total_sales'],
                name='as_sales_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='agentstats',
            index=models.Index(
                fields=['last_order_at'],
                name='as_last_order_idx'
            ),
        ),
        
        # ========================================
        # 约束
        # ========================================
        migrations.AddConstraint(
            model_name='agenttree',
            constraint=models.UniqueConstraint(
                fields=['site_id', 'agent', 'parent'],
                name='unique_site_agent_parent'
            ),
        ),
        
        # ========================================
        # RLS 策略 ⭐
        # ========================================
        migrations.RunSQL(
            sql="""
                -- 启用 RLS（agent_trees）
                ALTER TABLE agent_trees ENABLE ROW LEVEL SECURITY;
                ALTER TABLE agent_trees FORCE ROW LEVEL SECURITY;
                
                -- RLS 策略：站点隔离
                CREATE POLICY rls_agent_trees_site_isolation ON agent_trees
                    FOR ALL
                    USING (site_id = current_setting('app.current_site_id', true)::uuid)
                    WITH CHECK (site_id = current_setting('app.current_site_id', true)::uuid);
                
                -- Admin 只读策略
                CREATE POLICY rls_agent_trees_admin_read ON agent_trees
                    FOR SELECT
                    USING (pg_has_role(current_user, 'posx_admin', 'member'));
                
                -- 启用 RLS（agent_stats）
                ALTER TABLE agent_stats ENABLE ROW LEVEL SECURITY;
                ALTER TABLE agent_stats FORCE ROW LEVEL SECURITY;
                
                -- RLS 策略：站点隔离
                CREATE POLICY rls_agent_stats_site_isolation ON agent_stats
                    FOR ALL
                    USING (site_id = current_setting('app.current_site_id', true)::uuid)
                    WITH CHECK (site_id = current_setting('app.current_site_id', true)::uuid);
                
                -- Admin 只读策略
                CREATE POLICY rls_agent_stats_admin_read ON agent_stats
                    FOR SELECT
                    USING (pg_has_role(current_user, 'posx_admin', 'member'));
            """,
            reverse_sql="""
                -- 回滚 RLS
                ALTER TABLE agent_trees DISABLE ROW LEVEL SECURITY;
                ALTER TABLE agent_stats DISABLE ROW LEVEL SECURITY;
            """
        ),
    ]



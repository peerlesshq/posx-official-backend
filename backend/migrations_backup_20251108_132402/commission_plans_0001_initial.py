"""
佣金计划初始迁移

⭐ RLS 安全：
- commission_plans 和 commission_plan_tiers 表启用 RLS
- 通过 site_id 隔离（commission_plan_tiers 通过 plan.site_id 关联）
"""
from django.db import migrations, models
import django.core.validators
import uuid
from decimal import Decimal


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        # ========================================
        # 创建 commission_plans 表
        # ========================================
        migrations.CreateModel(
            name='CommissionPlan',
            fields=[
                ('plan_id', models.UUIDField(
                    primary_key=True,
                    default=uuid.uuid4,
                    editable=False,
                    help_text='计划唯一标识'
                )),
                ('site_id', models.UUIDField(
                    db_index=True,
                    help_text='站点ID（RLS隔离）'
                )),
                ('name', models.CharField(
                    max_length=100,
                    help_text='计划名称'
                )),
                ('version', models.PositiveIntegerField(
                    default=1,
                    help_text='版本号'
                )),
                ('mode', models.CharField(
                    max_length=20,
                    choices=[
                        ('level', 'Level-based'),
                        ('solar_diff', 'Solar Differential'),
                    ],
                    default='level',
                    help_text='计算模式'
                )),
                ('diff_reward_enabled', models.BooleanField(
                    default=False,
                    help_text='是否启用差额奖励'
                )),
                ('effective_from', models.DateTimeField(
                    null=True,
                    blank=True,
                    help_text='生效开始时间'
                )),
                ('effective_to', models.DateTimeField(
                    null=True,
                    blank=True,
                    help_text='生效结束时间'
                )),
                ('is_active', models.BooleanField(
                    default=False,
                    db_index=True,
                    help_text='激活状态'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'commission_plans',
                'verbose_name': 'Commission Plan',
                'verbose_name_plural': 'Commission Plans',
            },
        ),
        
        # ========================================
        # 创建 commission_plan_tiers 表
        # ========================================
        migrations.CreateModel(
            name='CommissionPlanTier',
            fields=[
                ('tier_id', models.UUIDField(
                    primary_key=True,
                    default=uuid.uuid4,
                    editable=False,
                    help_text='层级配置唯一标识'
                )),
                ('plan', models.ForeignKey(
                    on_delete=models.CASCADE,
                    related_name='tiers',
                    to='commission_plans.commissionplan',
                    help_text='所属计划'
                )),
                ('level', models.PositiveSmallIntegerField(
                    validators=[
                        django.core.validators.MinValueValidator(1),
                        django.core.validators.MaxValueValidator(10)
                    ],
                    help_text='层级（1-10）'
                )),
                ('rate_percent', models.DecimalField(
                    max_digits=5,
                    decimal_places=2,
                    validators=[
                        django.core.validators.MinValueValidator(Decimal('0')),
                        django.core.validators.MaxValueValidator(Decimal('100'))
                    ],
                    help_text='费率百分比（0-100）'
                )),
                ('min_sales', models.DecimalField(
                    max_digits=18,
                    decimal_places=6,
                    default=Decimal('0'),
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    help_text='该层级最低销售额'
                )),
                ('diff_cap_percent', models.DecimalField(
                    max_digits=5,
                    decimal_places=2,
                    null=True,
                    blank=True,
                    validators=[
                        django.core.validators.MinValueValidator(Decimal('0')),
                        django.core.validators.MaxValueValidator(Decimal('100'))
                    ],
                    help_text='差额封顶百分比（仅solar_diff模式）'
                )),
                ('hold_days', models.PositiveSmallIntegerField(
                    default=7,
                    help_text='佣金冻结天数'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'commission_plan_tiers',
                'ordering': ['level'],
                'verbose_name': 'Commission Plan Tier',
                'verbose_name_plural': 'Commission Plan Tiers',
            },
        ),
        
        # ========================================
        # 索引
        # ========================================
        migrations.AddIndex(
            model_name='commissionplan',
            index=models.Index(
                fields=['site_id', 'name', 'version'],
                name='cp_site_name_ver_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='commissionplan',
            index=models.Index(
                fields=['site_id', 'is_active'],
                name='cp_site_active_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='commissionplan',
            index=models.Index(
                fields=['effective_from', 'effective_to'],
                name='cp_effective_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='commissionplan',
            index=models.Index(
                fields=['created_at'],
                name='cp_created_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='commissionplantier',
            index=models.Index(
                fields=['plan', 'level'],
                name='cpt_plan_level_idx'
            ),
        ),
        
        # ========================================
        # 约束
        # ========================================
        migrations.AddConstraint(
            model_name='commissionplan',
            constraint=models.UniqueConstraint(
                fields=['site_id', 'name', 'version'],
                name='unique_site_plan_version'
            ),
        ),
        migrations.AddConstraint(
            model_name='commissionplantier',
            constraint=models.UniqueConstraint(
                fields=['plan', 'level'],
                name='unique_plan_level'
            ),
        ),
        
        # ========================================
        # RLS 策略 ⭐
        # ========================================
        migrations.RunSQL(
            sql="""
                -- 启用 RLS（commission_plans）
                ALTER TABLE commission_plans ENABLE ROW LEVEL SECURITY;
                ALTER TABLE commission_plans FORCE ROW LEVEL SECURITY;
                
                -- RLS 策略：站点隔离
                CREATE POLICY rls_commission_plans_site_isolation ON commission_plans
                    FOR ALL
                    USING (site_id = current_setting('app.current_site_id', true)::uuid)
                    WITH CHECK (site_id = current_setting('app.current_site_id', true)::uuid);
                
                -- Admin 只读策略
                CREATE POLICY rls_commission_plans_admin_read ON commission_plans
                    FOR SELECT
                    USING (pg_has_role(current_user, 'posx_admin', 'member'));
                
                -- 注意：commission_plan_tiers 通过 plan 外键关联，自动继承隔离
                -- 但为了安全，也显式启用 RLS
                ALTER TABLE commission_plan_tiers ENABLE ROW LEVEL SECURITY;
                ALTER TABLE commission_plan_tiers FORCE ROW LEVEL SECURITY;
                
                -- Tiers 策略：通过 plan 关联隔离
                CREATE POLICY rls_commission_plan_tiers_isolation ON commission_plan_tiers
                    FOR ALL
                    USING (
                        EXISTS (
                            SELECT 1 FROM commission_plans
                            WHERE commission_plans.plan_id = commission_plan_tiers.plan_id
                            AND commission_plans.site_id = current_setting('app.current_site_id', true)::uuid
                        )
                    )
                    WITH CHECK (
                        EXISTS (
                            SELECT 1 FROM commission_plans
                            WHERE commission_plans.plan_id = commission_plan_tiers.plan_id
                            AND commission_plans.site_id = current_setting('app.current_site_id', true)::uuid
                        )
                    );
                
                -- Admin 只读策略（tiers）
                CREATE POLICY rls_commission_plan_tiers_admin_read ON commission_plan_tiers
                    FOR SELECT
                    USING (pg_has_role(current_user, 'posx_admin', 'member'));
            """,
            reverse_sql="""
                -- 回滚 RLS
                ALTER TABLE commission_plans DISABLE ROW LEVEL SECURITY;
                ALTER TABLE commission_plan_tiers DISABLE ROW LEVEL SECURITY;
            """
        ),
    ]



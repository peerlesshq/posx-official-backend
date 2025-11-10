"""
Vesting释放计划生成服务

⭐ v2.2.1: 包含最后一期兜底逻辑
"""
import logging
from decimal import Decimal, ROUND_HALF_EVEN
from datetime import timedelta
from django.db import transaction
from django.utils import timezone

from apps.vesting.models import VestingSchedule, VestingRelease, VestingPolicy

logger = logging.getLogger(__name__)


def create_vesting_schedule(
    site,
    order,
    user,
    allocation,
    policy: VestingPolicy,
    total_tokens: Decimal
) -> VestingSchedule:
    """
    创建Vesting释放计划
    
    参数:
        site: 站点
        order: 订单
        user: 用户
        allocation: 分配记录
        policy: 释放策略
        total_tokens: 总代币数量
    
    返回:
        VestingSchedule 对象
    
    流程:
    1. 创建 VestingSchedule
    2. 生成多期 VestingRelease（含最后一期兜底）
    """
    # 1. 计算TGE和锁定代币
    tge_tokens = total_tokens * (policy.tge_percent / Decimal('100'))
    locked_tokens = total_tokens - tge_tokens
    
    # 2. 计算解锁开始日期（当前时间 + cliff_months）
    unlock_start_date = timezone.now().date()
    if policy.cliff_months > 0:
        unlock_start_date += timedelta(days=policy.cliff_months * 30)
    
    # 3. 创建Schedule
    with transaction.atomic():
        schedule = VestingSchedule.objects.create(
            site=site,
            order=order,
            user=user,
            allocation=allocation,
            policy=policy,
            total_tokens=total_tokens,
            tge_tokens=tge_tokens,
            locked_tokens=locked_tokens,
            unlock_start_date=unlock_start_date
        )
        
        # 4. 生成每期Release
        _generate_releases(schedule, policy, unlock_start_date)
        
        logger.info(
            f"[VestingService] Schedule created: {schedule.schedule_id}",
            extra={
                'schedule_id': str(schedule.schedule_id),
                'total_tokens': str(total_tokens),
                'tge_tokens': str(tge_tokens),
                'locked_tokens': str(locked_tokens),
                'periods': policy.linear_periods
            }
        )
    
    return schedule


def _generate_releases(
    schedule: VestingSchedule,
    policy: VestingPolicy,
    unlock_start: object
) -> None:
    """
    生成每期释放明细
    
    ⭐ v2.2.1: 最后一期兜底逻辑
    
    策略:
    1. Period 0: TGE立即释放（如果有）
    2. Period 1~(N-1): 标准等分，quantize到最小精度
    3. Period N: total - sum(previous) 兜底，确保总和精确
    
    参数:
        schedule: 释放计划
        policy: 释放策略
        unlock_start: 解锁开始日期
    """
    releases = []
    
    # Period 0: TGE（如果有）
    if schedule.tge_tokens > 0:
        releases.append(VestingRelease(
            schedule=schedule,
            period_no=0,
            release_date=timezone.now().date(),
            amount=schedule.tge_tokens,
            status=VestingRelease.STATUS_UNLOCKED  # TGE立即解锁
        ))
    
    # 线性释放期数
    if policy.linear_periods == 0:
        # 无线性释放，只有TGE
        VestingRelease.objects.bulk_create(releases)
        return
    
    # 计算每期标准金额
    per_period = schedule.locked_tokens / policy.linear_periods
    
    # ⭐ 量化到最小精度（0.000001）
    per_period_quantized = per_period.quantize(
        Decimal('0.000001'),
        rounding=ROUND_HALF_EVEN
    )
    
    # 累计金额（用于最后一期兜底）
    accumulated = Decimal('0')
    
    # Period 1 ~ (N-1): 标准分配
    current_date = unlock_start
    
    for i in range(1, policy.linear_periods):  # ⭐ 注意：到 N-1，不包括 N
        releases.append(VestingRelease(
            schedule=schedule,
            period_no=i,
            release_date=current_date,
            amount=per_period_quantized,
            status=VestingRelease.STATUS_LOCKED
        ))
        
        accumulated += per_period_quantized
        current_date = _next_period_date(current_date, policy)
    
    # ⭐ Period N: 最后一期兜底
    last_period_amount = schedule.locked_tokens - accumulated
    
    # 验证尾差不会过大（应该在 ±0.000001 范围内）
    if abs(last_period_amount - per_period_quantized) > Decimal('0.001'):
        logger.warning(
            f"[VestingService] Large tail difference detected",
            extra={
                'schedule_id': str(schedule.schedule_id),
                'expected': str(per_period_quantized),
                'actual': str(last_period_amount),
                'diff': str(last_period_amount - per_period_quantized)
            }
        )
    
    # 确保最后一期金额 >= 最小精度
    if last_period_amount < Decimal('0.000001'):
        raise ValueError(
            f"Last period amount too small: {last_period_amount}. "
            f"Check total_tokens and linear_periods configuration."
        )
    
    releases.append(VestingRelease(
        schedule=schedule,
        period_no=policy.linear_periods,
        release_date=current_date,
        amount=last_period_amount,  # ⭐ 精确兜底
        status=VestingRelease.STATUS_LOCKED
    ))
    
    # 批量创建
    VestingRelease.objects.bulk_create(releases)
    
    # ⭐ 验证总和
    total_check = sum(r.amount for r in releases)
    expected_total = schedule.tge_tokens + schedule.locked_tokens
    
    if total_check != expected_total:
        # 理论上不应该发生（因为有兜底）
        logger.error(
            f"[VestingService] Release sum mismatch!",
            extra={
                'schedule_id': str(schedule.schedule_id),
                'expected': str(expected_total),
                'actual': str(total_check),
                'diff': str(total_check - expected_total)
            }
        )
        raise ValueError(
            f"Release sum mismatch: {total_check} != {expected_total}"
        )
    
    logger.info(
        f"[VestingService] Generated {len(releases)} releases",
        extra={
            'schedule_id': str(schedule.schedule_id),
            'tge_count': 1 if schedule.tge_tokens > 0 else 0,
            'linear_count': policy.linear_periods,
            'last_period_amount': str(last_period_amount)
        }
    )


def _next_period_date(current_date, policy: VestingPolicy):
    """
    计算下一期释放日期
    
    参数:
        current_date: 当前日期
        policy: 释放策略
    
    返回:
        下一期日期
    """
    if policy.period_unit == 'day':
        return current_date + timedelta(days=1)
    elif policy.period_unit == 'week':
        return current_date + timedelta(days=7)
    elif policy.period_unit == 'month':
        return current_date + timedelta(days=30)
    else:
        raise ValueError(f"Unknown period_unit: {policy.period_unit}")


"""정책: ActiveTaskCount 과부하 판별 (설계서 §3, §4)."""

from task_soft_limit.policy.overload import is_overload

__all__ = ["is_overload"]

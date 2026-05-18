"""Unified priority grading rules for Campilot tasks."""


PRIORITY_LEVELS = [
    {
        "label": "特急",
        "rank": 0,
        "bonus": 30,
        "attention_window": 7,
        "advice": "需要立即处理，建议拆分任务并优先安排时间。",
    },
    {
        "label": "高",
        "rank": 1,
        "bonus": 24,
        "attention_window": 5,
        "advice": "建议优先处理，并在近期明确推进节点。",
    },
    {
        "label": "较高",
        "rank": 2,
        "bonus": 18,
        "attention_window": 3,
        "advice": "建议排入近期计划，避免临近截止时集中堆积。",
    },
    {
        "label": "中",
        "rank": 3,
        "bonus": 10,
        "attention_window": 1,
        "advice": "建议保持关注，按计划推进即可。",
    },
    {
        "label": "低",
        "rank": 4,
        "bonus": 5,
        "attention_window": 0,
        "advice": "暂时不需要优先处理，可在空档时间完成。",
    },
]

PRIORITY_LABELS = [level["label"] for level in PRIORITY_LEVELS]
DEFAULT_PRIORITY = "低"

_LEVEL_BY_LABEL = {level["label"]: level for level in PRIORITY_LEVELS}
_LEGACY_ALIASES = {
    "": DEFAULT_PRIORITY,
    "紧急": "特急",
    "最高": "特急",
    "很高": "特急",
    "中高": "较高",
    "较高": "较高",
    "高": "高",
    "中": "中",
    "低": "低",
}


def _safe_float(value, default=0.0):
    """Convert values from forms/DataFrames into a usable float."""
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _bounded_int(value, default=1, lower=1, upper=5):
    number = int(round(_safe_float(value, default)))
    return max(lower, min(upper, number))


def normalize_priority(priority):
    """Normalize old and new priority labels to the current five-level system."""
    text = str(priority or "").strip()
    return _LEGACY_ALIASES.get(text, text if text in _LEVEL_BY_LABEL else DEFAULT_PRIORITY)


def priority_rank(priority):
    """Return the lower-is-more-urgent rank for a priority label."""
    normalized = normalize_priority(priority)
    return int(_LEVEL_BY_LABEL.get(normalized, _LEVEL_BY_LABEL[DEFAULT_PRIORITY])["rank"])


def priority_bonus(priority):
    """Return the points bonus attached to a priority label."""
    normalized = normalize_priority(priority)
    return int(_LEVEL_BY_LABEL.get(normalized, _LEVEL_BY_LABEL[DEFAULT_PRIORITY])["bonus"])


def priority_attention_window(priority):
    """Return how many days ahead this priority should be recommended in timeline views."""
    normalized = normalize_priority(priority)
    return int(
        _LEVEL_BY_LABEL.get(normalized, _LEVEL_BY_LABEL[DEFAULT_PRIORITY])[
            "attention_window"
        ]
    )


def priority_advice(priority):
    """Return the user-facing action advice for a priority label."""
    normalized = normalize_priority(priority)
    return str(_LEVEL_BY_LABEL.get(normalized, _LEVEL_BY_LABEL[DEFAULT_PRIORITY])["advice"])


def is_high_impact_priority(priority):
    """Treat 特急 and 高 as high-impact priorities for achievements and stats."""
    return priority_rank(priority) <= priority_rank("高")


def calculate_priority_score(task_info):
    """
    Calculate a detailed pressure score from deadline, workload, difficulty and importance.

    The score is intentionally deterministic so every page can refresh active task
    priorities without waiting for a separate model or cached dataset to catch up.
    """
    days_left = int(round(_safe_float(task_info.get("days_left"), 9999)))
    estimated_hours = max(0.0, _safe_float(task_info.get("estimated_hours"), 0))
    difficulty = _bounded_int(task_info.get("difficulty"), default=1)
    importance = _bounded_int(task_info.get("importance"), default=1)
    task_type = str(task_info.get("task_type", "事务")).strip()

    if days_left < 0:
        urgency_score = 62
    elif days_left == 0:
        urgency_score = 58
    elif days_left == 1:
        urgency_score = 48
    elif days_left <= 3:
        urgency_score = 38
    elif days_left <= 5:
        urgency_score = 28
    elif days_left <= 7:
        urgency_score = 18
    elif days_left <= 14:
        urgency_score = 8
    else:
        urgency_score = 0

    if estimated_hours >= 8:
        workload_score = 18
    elif estimated_hours >= 5:
        workload_score = 14
    elif estimated_hours >= 3:
        workload_score = 9
    elif estimated_hours >= 1.5:
        workload_score = 5
    elif estimated_hours > 0:
        workload_score = 2
    else:
        workload_score = 0

    type_boosts = {
        "报告": 4,
        "项目": 4,
        "实验": 3,
        "作业": 3,
        "复习": 2,
        "预习": 1,
        "阅读": 1,
        "事务": 0,
    }

    return (
        urgency_score
        + importance * 8
        + difficulty * 5
        + workload_score
        + type_boosts.get(task_type, 0)
    )


def grade_priority(task_info):
    """Return a five-level priority label for task information."""
    days_left = int(round(_safe_float(task_info.get("days_left"), 9999)))
    estimated_hours = max(0.0, _safe_float(task_info.get("estimated_hours"), 0))
    difficulty = _bounded_int(task_info.get("difficulty"), default=1)
    importance = _bounded_int(task_info.get("importance"), default=1)
    score = calculate_priority_score(task_info)

    if days_left <= 0 and (importance >= 4 or difficulty >= 4 or estimated_hours >= 2.5):
        return "特急"
    if days_left <= 0:
        return "高"
    if days_left <= 1 and importance >= 5 and (difficulty >= 3 or estimated_hours >= 2):
        return "特急"
    if days_left <= 2 and importance >= 4 and estimated_hours >= 4:
        return "特急"

    if score >= 112:
        return "特急"
    if score >= 92:
        return "高"
    if score >= 72:
        return "较高"
    if score >= 48:
        return "中"
    return "低"

"""Campilot 数据读写与业务逻辑层。"""

import json
from calendar import monthrange
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from model import predict_priority, train_priority_model


DATA_DIR = Path("data")
USER_TASKS_PATH = DATA_DIR / "user_tasks.csv"
FIXED_EVENTS_PATH = DATA_DIR / "fixed_events.csv"
REWARDS_PATH = DATA_DIR / "rewards.csv"
REDEMPTION_PATH = DATA_DIR / "redemption_records.csv"
USER_STATS_PATH = DATA_DIR / "user_stats.json"

TASK_COLUMNS = [
    "task_id",
    "task_name",
    "tag",
    "task_type",
    "deadline",
    "days_left",
    "estimated_hours",
    "difficulty",
    "importance",
    "priority",
    "reason",
    "status",
    "created_at",
    "completed_at",
    "actual_hours",
    "points",
    "note",
]

EVENT_COLUMNS = [
    "event_id",
    "event_name",
    "event_type",
    "date",
    "start_time",
    "end_time",
    "note",
    "is_repeated",
    "repeat_group_id",
    "created_at",
]

REWARD_COLUMNS = ["reward_id", "reward_name", "cost", "description"]
REDEMPTION_COLUMNS = ["record_id", "reward_name", "cost", "redeemed_at"]

DEFAULT_REWARDS = [
    {"reward_id": 1, "reward_name": "一杯喜欢的饮品", "cost": 80, "description": "完成任务后的短时奖励"},
    {"reward_id": 2, "reward_name": "一顿想吃的饭", "cost": 120, "description": "用一顿饭恢复能量"},
    {"reward_id": 3, "reward_name": "一次校外散步", "cost": 200, "description": "离开校园散步放松"},
    {"reward_id": 4, "reward_name": "一次半日出游", "cost": 300, "description": "安排一次较长时间的恢复活动"},
]

DEFAULT_USER_STATS = {"current_points": 0, "total_points": 0, "completed_tasks": 0}
PRIORITY_BONUS = {"高": 20, "中": 10, "低": 5}
EVENT_TYPE_OPTIONS = {"课程", "会议", "社交", "生活", "其他"}
REPEAT_FREQUENCY_OPTIONS = {"daily", "weekly", "monthly"}
REPEAT_END_TYPE_OPTIONS = {"count", "until"}
MAX_REPEAT_EVENT_COUNT = 60

_CACHED_MODEL = None


def _now_str():
    """返回当前时间字符串。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _next_id(df, id_col):
    """根据现有 DataFrame 计算下一个整数 ID。"""
    if df.empty or id_col not in df.columns:
        return 1
    ids = pd.to_numeric(df[id_col], errors="coerce").dropna()
    if ids.empty:
        return 1
    return int(ids.max()) + 1


def _find_row_index(df, id_col, target_id):
    """按 ID 查找行索引；未找到返回 None。"""
    if id_col not in df.columns:
        return None
    matched_index = df.index[df[id_col].astype(str) == str(target_id)]
    if matched_index.empty:
        return None
    return int(matched_index[0])


def _row_to_dict(row):
    """将 DataFrame 单行转换为字典，并将 NaN 转为 None。"""
    result = {}
    for key, value in row.items():
        if pd.isna(value):
            result[key] = None
        else:
            if hasattr(value, "item"):
                value = value.item()
            result[key] = value
    return result


def _get_prediction_model():
    """懒加载并缓存优先级模型，避免每次新增任务都重复训练。"""
    global _CACHED_MODEL
    if _CACHED_MODEL is None:
        _CACHED_MODEL, _ = train_priority_model()
    return _CACHED_MODEL


def _save_redemption_records(df):
    """保存兑换记录。"""
    save_df = df.copy()
    for col in REDEMPTION_COLUMNS:
        if col not in save_df.columns:
            save_df[col] = ""
    save_df = save_df[REDEMPTION_COLUMNS]
    save_df.to_csv(REDEMPTION_PATH, index=False, encoding="utf-8-sig")


def _normalize_tasks_df(df):
    """标准化任务表结构与常见字段类型。"""
    normalized = df.copy()

    for col in TASK_COLUMNS:
        if col not in normalized.columns:
            normalized[col] = ""
    normalized = normalized[TASK_COLUMNS]

    text_cols = [
        "task_name",
        "tag",
        "task_type",
        "deadline",
        "priority",
        "reason",
        "status",
        "created_at",
        "completed_at",
        "note",
    ]
    for col in text_cols:
        normalized[col] = normalized[col].fillna("").astype(str)

    normalized["task_id"] = pd.to_numeric(normalized["task_id"], errors="coerce")
    normalized["days_left"] = pd.to_numeric(normalized["days_left"], errors="coerce")
    normalized["estimated_hours"] = pd.to_numeric(normalized["estimated_hours"], errors="coerce")
    normalized["difficulty"] = pd.to_numeric(normalized["difficulty"], errors="coerce")
    normalized["importance"] = pd.to_numeric(normalized["importance"], errors="coerce")
    normalized["actual_hours"] = pd.to_numeric(normalized["actual_hours"], errors="coerce")
    normalized["points"] = pd.to_numeric(normalized["points"], errors="coerce").fillna(0).astype(int)

    return normalized


def _refresh_days_left(df):
    """按当前日期实时刷新 days_left。"""
    refreshed = df.copy()
    deadline_series = pd.to_datetime(refreshed["deadline"], errors="coerce")
    today_ts = pd.Timestamp(date.today())
    refreshed["days_left"] = (deadline_series - today_ts).dt.days
    return refreshed


def _to_bool(value):
    """将常见输入安全转为布尔值。"""
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "是"}


def _parse_date_or_raise(value, field_name):
    """解析日期字段（YYYY-MM-DD）。"""
    text = str(value).strip()
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{field_name} 格式无效，请使用 YYYY-MM-DD") from exc


def _parse_time_or_raise(value, field_name):
    """解析时间字段（HH:MM 或 HH:MM:SS）。"""
    text = str(value).strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"{field_name} 格式无效，请使用 HH:MM")


def _parse_positive_int(value, field_name, max_value=None):
    """解析正整数并做上限校验。"""
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} 必须为正整数") from exc
    if number <= 0:
        raise ValueError(f"{field_name} 必须为正整数")
    if max_value is not None and number > max_value:
        raise ValueError(f"{field_name} 不能超过 {max_value}")
    return number


def _normalize_repeat_frequency(value):
    """标准化重复频率值。"""
    mapping = {
        "daily": "daily",
        "每天": "daily",
        "weekly": "weekly",
        "每周": "weekly",
        "monthly": "monthly",
        "每月": "monthly",
    }
    normalized = mapping.get(str(value).strip().lower())
    if normalized not in REPEAT_FREQUENCY_OPTIONS:
        raise ValueError("repeat_frequency 仅支持 每天 / 每周 / 每月")
    return normalized


def _normalize_repeat_end_type(value):
    """标准化重复结束方式。"""
    mapping = {
        "count": "count",
        "按次数结束": "count",
        "until": "until",
        "按日期结束": "until",
    }
    normalized = mapping.get(str(value).strip().lower(), str(value).strip())
    if normalized not in REPEAT_END_TYPE_OPTIONS:
        raise ValueError("repeat_end_type 仅支持 按次数结束 / 按日期结束")
    return normalized


def _normalize_repeat_weekdays(values):
    """标准化每周重复的星期参数（0-6，周一到周日）。"""
    if values is None:
        values = []
    if not isinstance(values, (list, tuple, set)):
        values = [values]

    weekday_aliases = {
        "0": 0,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "周一": 0,
        "周二": 1,
        "周三": 2,
        "周四": 3,
        "周五": 4,
        "周六": 5,
        "周日": 6,
        "星期一": 0,
        "星期二": 1,
        "星期三": 2,
        "星期四": 3,
        "星期五": 4,
        "星期六": 5,
        "星期日": 6,
    }

    normalized = set()
    for item in values:
        text = str(item).strip()
        if text in weekday_aliases:
            normalized.add(weekday_aliases[text])

    return sorted(normalized)


def _validate_event_time_range(start_time, end_time):
    """校验固定安排时间段：仅支持同一天内结束时间晚于开始时间。"""
    if end_time <= start_time:
        raise ValueError("end_time 必须晚于 start_time，且暂不支持跨天安排")


def _normalize_event_input(event_data):
    """标准化并校验固定安排通用字段。"""
    event_name = str(event_data.get("event_name", "")).strip()
    if not event_name:
        raise ValueError("event_name 不能为空")

    event_type = str(event_data.get("event_type", "")).strip()
    if event_type not in EVENT_TYPE_OPTIONS:
        event_type = "其他"

    event_date = _parse_date_or_raise(event_data.get("date", ""), "date")
    start_time_obj = _parse_time_or_raise(event_data.get("start_time", ""), "start_time")
    end_time_obj = _parse_time_or_raise(event_data.get("end_time", ""), "end_time")
    _validate_event_time_range(start_time_obj, end_time_obj)

    return {
        "event_name": event_name,
        "event_type": event_type,
        "date": event_date,
        "start_time": start_time_obj.strftime("%H:%M"),
        "end_time": end_time_obj.strftime("%H:%M"),
        "note": str(event_data.get("note", "")).strip(),
    }


def _parse_repeat_config(event_data, start_date):
    """解析重复规则与结束方式。"""
    repeat_frequency = _normalize_repeat_frequency(event_data.get("repeat_frequency", ""))
    repeat_interval = _parse_positive_int(
        event_data.get("repeat_interval", 1), "repeat_interval"
    )
    repeat_end_type = _normalize_repeat_end_type(event_data.get("repeat_end_type", "count"))

    repeat_weekdays = []
    if repeat_frequency == "weekly":
        repeat_weekdays = _normalize_repeat_weekdays(event_data.get("repeat_weekdays"))
        if not repeat_weekdays:
            raise ValueError("每周重复时，必须至少选择一个星期")

    repeat_count = None
    repeat_until = None
    if repeat_end_type == "count":
        repeat_count = _parse_positive_int(
            event_data.get("repeat_count", 1),
            "repeat_count",
            max_value=MAX_REPEAT_EVENT_COUNT,
        )
    else:
        repeat_until = _parse_date_or_raise(event_data.get("repeat_until", ""), "repeat_until")
        if repeat_until < start_date:
            raise ValueError("repeat_until 不能早于开始日期")

    return {
        "repeat_frequency": repeat_frequency,
        "repeat_interval": repeat_interval,
        "repeat_weekdays": repeat_weekdays,
        "repeat_end_type": repeat_end_type,
        "repeat_count": repeat_count,
        "repeat_until": repeat_until,
    }


def _generate_daily_dates(start_date, repeat_interval, repeat_end_type, repeat_count, repeat_until):
    """生成按天重复的日期序列。"""
    if repeat_end_type == "count":
        return [start_date + timedelta(days=repeat_interval * i) for i in range(repeat_count)]

    dates = []
    current = start_date
    while current <= repeat_until:
        if len(dates) >= MAX_REPEAT_EVENT_COUNT:
            raise ValueError(f"按日期结束最多生成 {MAX_REPEAT_EVENT_COUNT} 条固定安排")
        dates.append(current)
        current = current + timedelta(days=repeat_interval)
    return dates


def _generate_weekly_dates(start_date, repeat_interval, repeat_weekdays, repeat_end_type, repeat_count, repeat_until):
    """生成按周重复的日期序列（支持多选星期）。"""
    start_week_monday = start_date - timedelta(days=start_date.weekday())
    weekday_list = sorted(set(repeat_weekdays))
    dates = []
    interval_index = 0

    while True:
        week_base = start_week_monday + timedelta(weeks=interval_index * repeat_interval)
        if repeat_end_type == "until" and week_base > repeat_until + timedelta(days=6):
            break

        for weekday in weekday_list:
            candidate = week_base + timedelta(days=weekday)
            if candidate < start_date:
                continue
            if repeat_end_type == "until" and candidate > repeat_until:
                continue

            if len(dates) >= MAX_REPEAT_EVENT_COUNT:
                raise ValueError(f"按日期结束最多生成 {MAX_REPEAT_EVENT_COUNT} 条固定安排")

            dates.append(candidate)
            if repeat_end_type == "count" and len(dates) >= repeat_count:
                return dates

        interval_index += 1
    return dates


def _generate_monthly_dates(start_date, repeat_interval, repeat_end_type, repeat_count, repeat_until):
    """生成按月重复的日期序列（按开始日重复，缺失日期月份跳过）。"""
    target_day = start_date.day
    start_month_index = start_date.year * 12 + (start_date.month - 1)
    dates = []
    step = 0

    while True:
        month_index = start_month_index + step * repeat_interval
        year = month_index // 12
        month = (month_index % 12) + 1

        if repeat_end_type == "until":
            until_month_index = repeat_until.year * 12 + (repeat_until.month - 1)
            if month_index > until_month_index:
                break

        days_in_month = monthrange(year, month)[1]
        if target_day <= days_in_month:
            candidate = date(year, month, target_day)
            if candidate >= start_date:
                if repeat_end_type == "until":
                    if candidate > repeat_until:
                        break
                    if len(dates) >= MAX_REPEAT_EVENT_COUNT:
                        raise ValueError(
                            f"按日期结束最多生成 {MAX_REPEAT_EVENT_COUNT} 条固定安排"
                        )
                    dates.append(candidate)
                else:
                    dates.append(candidate)
                    if len(dates) >= repeat_count:
                        return dates

        step += 1
    return dates


def _generate_repeat_dates(start_date, repeat_config):
    """按重复规则生成日期列表。"""
    frequency = repeat_config["repeat_frequency"]
    repeat_interval = repeat_config["repeat_interval"]
    end_type = repeat_config["repeat_end_type"]
    repeat_count = repeat_config["repeat_count"]
    repeat_until = repeat_config["repeat_until"]
    repeat_weekdays = repeat_config["repeat_weekdays"]

    if frequency == "daily":
        return _generate_daily_dates(
            start_date, repeat_interval, end_type, repeat_count, repeat_until
        )
    if frequency == "weekly":
        return _generate_weekly_dates(
            start_date,
            repeat_interval,
            repeat_weekdays,
            end_type,
            repeat_count,
            repeat_until,
        )
    return _generate_monthly_dates(
        start_date, repeat_interval, end_type, repeat_count, repeat_until
    )


def _next_repeat_group_id(events_df):
    """计算新的重复分组 ID。"""
    if events_df.empty or "repeat_group_id" not in events_df.columns:
        return 1
    group_ids = pd.to_numeric(events_df["repeat_group_id"], errors="coerce").dropna()
    if group_ids.empty:
        return 1
    return int(group_ids.max()) + 1


def _build_new_event_rows(event_data, events_df, force_repeated=None):
    """根据输入数据构建一条或多条固定安排记录。"""
    normalized_input = _normalize_event_input(event_data)
    start_date = normalized_input["date"]
    is_repeated = _to_bool(event_data.get("is_repeated", False))
    if force_repeated is not None:
        is_repeated = bool(force_repeated)

    repeat_group_id = pd.NA
    dates = [start_date]
    if is_repeated:
        repeat_config = _parse_repeat_config(event_data, start_date)
        dates = _generate_repeat_dates(start_date, repeat_config)
        repeat_group_id = _next_repeat_group_id(events_df)

    start_event_id = _next_id(events_df, "event_id")
    created_at = _now_str()
    rows = []
    for idx, event_date in enumerate(dates):
        rows.append(
            {
                "event_id": start_event_id + idx,
                "event_name": normalized_input["event_name"],
                "event_type": normalized_input["event_type"],
                "date": event_date.isoformat(),
                "start_time": normalized_input["start_time"],
                "end_time": normalized_input["end_time"],
                "note": normalized_input["note"],
                "is_repeated": bool(is_repeated),
                "repeat_group_id": repeat_group_id if is_repeated else pd.NA,
                "created_at": created_at,
            }
        )
    return rows


def _normalize_events_df(df):
    """标准化固定安排表结构与字段类型。"""
    normalized = df.copy()
    for col in EVENT_COLUMNS:
        if col not in normalized.columns:
            normalized[col] = ""
    normalized = normalized[EVENT_COLUMNS]

    normalized["event_id"] = pd.to_numeric(normalized["event_id"], errors="coerce")
    for col in ["event_name", "date", "start_time", "end_time", "event_type", "note", "created_at"]:
        normalized[col] = normalized[col].fillna("").astype(str)

    normalized["event_type"] = normalized["event_type"].apply(
        lambda value: value if value in EVENT_TYPE_OPTIONS else "其他"
    )
    normalized["is_repeated"] = normalized["is_repeated"].apply(_to_bool)
    normalized["repeat_group_id"] = pd.to_numeric(
        normalized["repeat_group_id"], errors="coerce"
    )

    return normalized


def _normalize_redemption_df(df):
    """标准化兑换记录表结构与字段类型。"""
    normalized = df.copy()
    for col in REDEMPTION_COLUMNS:
        if col not in normalized.columns:
            normalized[col] = ""
    normalized = normalized[REDEMPTION_COLUMNS]
    normalized["record_id"] = pd.to_numeric(normalized["record_id"], errors="coerce")
    normalized["cost"] = pd.to_numeric(normalized["cost"], errors="coerce")
    normalized["reward_name"] = normalized["reward_name"].fillna("").astype(str)
    normalized["redeemed_at"] = normalized["redeemed_at"].fillna("").astype(str)
    return normalized


def ensure_data_files():
    """
    确保 Campilot 数据目录和基础数据文件存在，不存在时自动初始化。
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not USER_TASKS_PATH.exists():
        pd.DataFrame(columns=TASK_COLUMNS).to_csv(
            USER_TASKS_PATH, index=False, encoding="utf-8-sig"
        )

    if not FIXED_EVENTS_PATH.exists():
        pd.DataFrame(columns=EVENT_COLUMNS).to_csv(
            FIXED_EVENTS_PATH, index=False, encoding="utf-8-sig"
        )

    if not REWARDS_PATH.exists():
        pd.DataFrame(DEFAULT_REWARDS, columns=REWARD_COLUMNS).to_csv(
            REWARDS_PATH, index=False, encoding="utf-8-sig"
        )

    if not REDEMPTION_PATH.exists():
        pd.DataFrame(columns=REDEMPTION_COLUMNS).to_csv(
            REDEMPTION_PATH, index=False, encoding="utf-8-sig"
        )

    if not USER_STATS_PATH.exists():
        with USER_STATS_PATH.open("w", encoding="utf-8") as file:
            json.dump(DEFAULT_USER_STATS, file, ensure_ascii=False, indent=2)


def load_tasks():
    """
    读取任务数据。

    Returns:
        pandas.DataFrame: user_tasks.csv 对应数据。
    """
    ensure_data_files()
    df = pd.read_csv(USER_TASKS_PATH, encoding="utf-8-sig")
    normalized = _normalize_tasks_df(df)
    return _refresh_days_left(normalized)


def save_tasks(df):
    """
    保存任务数据。

    Args:
        df (pandas.DataFrame): 任务数据表。
    """
    ensure_data_files()
    save_df = _normalize_tasks_df(df)
    save_df.to_csv(USER_TASKS_PATH, index=False, encoding="utf-8-sig")


def add_task(task_data):
    """
    新增任务并自动预测优先级。

    Args:
        task_data (dict): 包含 task_name, tag, task_type, deadline, estimated_hours,
            difficulty, importance, note。

    Returns:
        dict: 新增后的完整任务字典。
    """
    tasks_df = load_tasks()
    task_id = _next_id(tasks_df, "task_id")

    deadline_raw = task_data.get("deadline")
    try:
        deadline_date = pd.to_datetime(deadline_raw).date()
    except Exception as exc:
        raise ValueError("deadline 格式无效，请使用 YYYY-MM-DD") from exc

    days_left = (deadline_date - date.today()).days
    estimated_hours = float(task_data.get("estimated_hours", 0))
    difficulty = int(task_data.get("difficulty", 1))
    importance = int(task_data.get("importance", 1))
    task_type = str(task_data.get("task_type", "事务"))

    task_info_for_model = {
        "days_left": days_left,
        "estimated_hours": estimated_hours,
        "difficulty": difficulty,
        "importance": importance,
        "task_type": task_type,
    }

    prediction = predict_priority(task_info_for_model, model=_get_prediction_model())
    created_at = _now_str()

    new_task = {
        "task_id": task_id,
        "task_name": task_data.get("task_name", ""),
        "tag": task_data.get("tag", ""),
        "task_type": task_type,
        "deadline": deadline_date.isoformat(),
        "days_left": days_left,
        "estimated_hours": estimated_hours,
        "difficulty": difficulty,
        "importance": importance,
        "priority": prediction["priority"],
        "reason": prediction["reason"],
        "status": "未完成",
        "created_at": created_at,
        "completed_at": "",
        "actual_hours": "",
        "points": 0,
        "note": task_data.get("note", ""),
    }

    tasks_df = pd.concat([tasks_df, pd.DataFrame([new_task])], ignore_index=True)
    save_tasks(tasks_df)
    return new_task


def update_task_status(task_id, status):
    """
    更新任务状态。

    Args:
        task_id: 任务 ID。
        status (str): 新状态。

    Returns:
        dict: 更新后的任务字典。
    """
    tasks_df = load_tasks()
    index = _find_row_index(tasks_df, "task_id", task_id)
    if index is None:
        raise ValueError(f"未找到 task_id={task_id} 的任务")

    tasks_df.at[index, "status"] = status
    if status != "已完成":
        tasks_df.at[index, "completed_at"] = ""

    save_tasks(tasks_df)
    return _row_to_dict(tasks_df.loc[index])


def update_task(task_id, updated_data, recalculate_priority=True):
    """
    更新任务信息。

    Args:
        task_id: 任务 ID。
        updated_data (dict): 允许更新的字段，包含 task_name/tag/task_type/deadline/
            estimated_hours/difficulty/importance/status/note 等。
        recalculate_priority (bool): 是否重新计算优先级和推荐理由。

    Returns:
        dict: 更新后的任务字典。
    """
    tasks_df = load_tasks()
    index = _find_row_index(tasks_df, "task_id", task_id)
    if index is None:
        raise ValueError(f"未找到 task_id={task_id} 的任务")

    # 文本字段更新
    for text_col in ["task_name", "tag", "task_type", "status", "note"]:
        if text_col in updated_data:
            tasks_df.at[index, text_col] = str(updated_data.get(text_col, "")).strip()

    # 数值与日期字段更新
    current_deadline = str(tasks_df.at[index, "deadline"])
    deadline_raw = str(updated_data.get("deadline", current_deadline)).strip()
    try:
        deadline_date = pd.to_datetime(deadline_raw).date()
    except Exception as exc:
        raise ValueError("deadline 格式无效，请使用 YYYY-MM-DD") from exc

    estimated_hours = float(
        updated_data.get("estimated_hours", tasks_df.at[index, "estimated_hours"])
    )
    difficulty = int(float(updated_data.get("difficulty", tasks_df.at[index, "difficulty"])))
    importance = int(float(updated_data.get("importance", tasks_df.at[index, "importance"])))

    tasks_df.at[index, "deadline"] = deadline_date.isoformat()
    tasks_df.at[index, "estimated_hours"] = estimated_hours
    tasks_df.at[index, "difficulty"] = difficulty
    tasks_df.at[index, "importance"] = importance
    tasks_df.at[index, "days_left"] = (deadline_date - date.today()).days

    if recalculate_priority:
        task_info_for_model = {
            "days_left": int(tasks_df.at[index, "days_left"]),
            "estimated_hours": float(tasks_df.at[index, "estimated_hours"]),
            "difficulty": int(float(tasks_df.at[index, "difficulty"])),
            "importance": int(float(tasks_df.at[index, "importance"])),
            "task_type": str(tasks_df.at[index, "task_type"]),
        }
        prediction = predict_priority(task_info_for_model, model=_get_prediction_model())
        tasks_df.at[index, "priority"] = prediction["priority"]
        tasks_df.at[index, "reason"] = prediction["reason"]

    save_tasks(tasks_df)
    return _row_to_dict(tasks_df.loc[index])


def calculate_task_points(task_row):
    """
    根据任务信息计算积分。

    公式：difficulty * 10 + importance * 5 + priority_bonus
    """
    difficulty = int(float(task_row["difficulty"]))
    importance = int(float(task_row["importance"]))
    priority = str(task_row["priority"])
    priority_bonus = PRIORITY_BONUS.get(priority, 5)
    return difficulty * 10 + importance * 5 + priority_bonus


def complete_task(task_id, actual_hours=None):
    """
    完成任务并发放积分，更新用户统计。

    Args:
        task_id: 任务 ID。
        actual_hours: 实际耗时（可选）。

    Returns:
        dict: 完成后的任务字典。
    """
    tasks_df = load_tasks()
    index = _find_row_index(tasks_df, "task_id", task_id)
    if index is None:
        raise ValueError(f"未找到 task_id={task_id} 的任务")

    current_status = str(tasks_df.at[index, "status"])
    if current_status == "已完成":
        if actual_hours is not None:
            tasks_df.at[index, "actual_hours"] = float(actual_hours)
            save_tasks(tasks_df)
        return _row_to_dict(tasks_df.loc[index])

    points = calculate_task_points(tasks_df.loc[index])
    tasks_df.at[index, "status"] = "已完成"
    tasks_df.at[index, "completed_at"] = _now_str()
    tasks_df.at[index, "points"] = points
    if actual_hours is not None:
        tasks_df.at[index, "actual_hours"] = float(actual_hours)

    save_tasks(tasks_df)

    stats = load_user_stats()
    stats["current_points"] = int(stats.get("current_points", 0)) + int(points)
    stats["total_points"] = int(stats.get("total_points", 0)) + int(points)
    stats["completed_tasks"] = int(stats.get("completed_tasks", 0)) + 1
    save_user_stats(stats)

    return _row_to_dict(tasks_df.loc[index])


def delete_task(task_id):
    """
    删除任务。

    Args:
        task_id: 任务 ID。

    Returns:
        bool: 是否删除成功。
    """
    tasks_df = load_tasks()
    original_count = len(tasks_df)
    tasks_df = tasks_df[tasks_df["task_id"].astype(str) != str(task_id)].copy()

    if len(tasks_df) == original_count:
        return False

    save_tasks(tasks_df)
    return True


def load_events():
    """
    读取固定安排数据。

    Returns:
        pandas.DataFrame: fixed_events.csv 对应数据。
    """
    ensure_data_files()
    df = pd.read_csv(FIXED_EVENTS_PATH, encoding="utf-8-sig")
    normalized = _normalize_events_df(df)
    return normalized.sort_values(
        by=["date", "start_time", "event_id"], kind="stable"
    ).reset_index(drop=True)


def save_events(df):
    """
    保存固定安排数据。

    Args:
        df (pandas.DataFrame): 固定安排数据表。
    """
    ensure_data_files()
    save_df = _normalize_events_df(df)
    save_df.to_csv(FIXED_EVENTS_PATH, index=False, encoding="utf-8-sig")


def add_event(event_data):
    """
    新增固定安排。

    Args:
        event_data (dict): 包含 event_name, event_type, date, start_time, end_time, note
            及可选重复参数。

    Returns:
        list[dict]: 新增后的固定安排字典列表。
    """
    events_df = load_events()
    new_rows = _build_new_event_rows(event_data, events_df)

    events_df = pd.concat([events_df, pd.DataFrame(new_rows)], ignore_index=True)
    save_events(events_df)
    return new_rows


def update_event(event_id, event_data, update_scope="single"):
    """
    更新固定安排。

    Args:
        event_id: 固定安排 ID。
        event_data (dict): 更新后的字段。
        update_scope (str): 更新范围，single 或 group。

    Returns:
        dict: 更新结果摘要。
    """
    events_df = load_events()
    index = _find_row_index(events_df, "event_id", event_id)
    if index is None:
        raise ValueError(f"未找到 event_id={event_id} 的固定安排")

    target_row = events_df.loc[index]
    normalized_input = _normalize_event_input(event_data)
    scope = str(update_scope or "single").strip().lower()
    source_is_repeated = _to_bool(target_row.get("is_repeated", False))
    target_is_repeated = _to_bool(event_data.get("is_repeated", source_is_repeated))

    if (
        scope == "group"
        and source_is_repeated
        and pd.notna(target_row.get("repeat_group_id"))
    ):
        target_group_id = int(float(target_row.get("repeat_group_id")))
        group_mask = (
            pd.to_numeric(events_df["repeat_group_id"], errors="coerce") == target_group_id
        )
        remaining_df = events_df[~group_mask].copy()

        group_payload = dict(event_data)
        group_payload["event_name"] = normalized_input["event_name"]
        group_payload["event_type"] = normalized_input["event_type"]
        group_payload["date"] = normalized_input["date"].isoformat()
        group_payload["start_time"] = normalized_input["start_time"]
        group_payload["end_time"] = normalized_input["end_time"]
        group_payload["note"] = normalized_input["note"]
        group_payload["is_repeated"] = target_is_repeated

        regenerated_rows = _build_new_event_rows(
            group_payload, remaining_df, force_repeated=target_is_repeated
        )
        updated_df = pd.concat([remaining_df, pd.DataFrame(regenerated_rows)], ignore_index=True)
        save_events(updated_df)
        return {
            "mode": "group",
            "updated_count": len(regenerated_rows),
            "repeat_group_id": regenerated_rows[0]["repeat_group_id"] if regenerated_rows else None,
        }

    if not source_is_repeated and target_is_repeated:
        remaining_df = events_df[events_df["event_id"].astype(str) != str(event_id)].copy()
        promote_payload = dict(event_data)
        promote_payload["event_name"] = normalized_input["event_name"]
        promote_payload["event_type"] = normalized_input["event_type"]
        promote_payload["date"] = normalized_input["date"].isoformat()
        promote_payload["start_time"] = normalized_input["start_time"]
        promote_payload["end_time"] = normalized_input["end_time"]
        promote_payload["note"] = normalized_input["note"]
        promote_payload["is_repeated"] = True

        regenerated_rows = _build_new_event_rows(
            promote_payload, remaining_df, force_repeated=True
        )
        updated_df = pd.concat([remaining_df, pd.DataFrame(regenerated_rows)], ignore_index=True)
        save_events(updated_df)
        return {
            "mode": "single_to_group",
            "updated_count": len(regenerated_rows),
            "repeat_group_id": regenerated_rows[0]["repeat_group_id"] if regenerated_rows else None,
        }

    events_df.at[index, "event_name"] = normalized_input["event_name"]
    events_df.at[index, "event_type"] = normalized_input["event_type"]
    events_df.at[index, "date"] = normalized_input["date"].isoformat()
    events_df.at[index, "start_time"] = normalized_input["start_time"]
    events_df.at[index, "end_time"] = normalized_input["end_time"]
    events_df.at[index, "note"] = normalized_input["note"]
    if source_is_repeated and target_is_repeated:
        events_df.at[index, "is_repeated"] = True
    elif source_is_repeated and not target_is_repeated:
        events_df.at[index, "is_repeated"] = False
        events_df.at[index, "repeat_group_id"] = pd.NA
    else:
        events_df.at[index, "is_repeated"] = False
        events_df.at[index, "repeat_group_id"] = pd.NA
    save_events(events_df)
    return {"mode": "single", "updated_count": 1}


def delete_event(event_id, delete_scope="single"):
    """
    删除固定安排。

    Args:
        event_id: 固定安排 ID。
        delete_scope (str): 删除范围，single 或 group。

    Returns:
        int: 删除条数（0 表示未删除）。
    """
    events_df = load_events()
    index = _find_row_index(events_df, "event_id", event_id)
    if index is None:
        return 0

    target_row = events_df.loc[index]
    scope = str(delete_scope or "single").strip().lower()
    if (
        scope == "group"
        and _to_bool(target_row.get("is_repeated", False))
        and pd.notna(target_row.get("repeat_group_id"))
    ):
        target_group_id = int(float(target_row.get("repeat_group_id")))
        group_mask = (
            pd.to_numeric(events_df["repeat_group_id"], errors="coerce") == target_group_id
        )
        deleted_count = int(group_mask.sum())
        if deleted_count <= 0:
            return 0
        remaining_df = events_df[~group_mask].copy()
        save_events(remaining_df)
        return deleted_count

    remaining_df = events_df[events_df["event_id"].astype(str) != str(event_id)].copy()
    deleted_count = len(events_df) - len(remaining_df)
    if deleted_count > 0:
        save_events(remaining_df)
    return deleted_count


def load_user_stats():
    """
    读取用户积分统计信息。

    Returns:
        dict: 用户统计信息。
    """
    ensure_data_files()
    with USER_STATS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_user_stats(stats):
    """
    保存用户积分统计信息。

    Args:
        stats (dict): 用户统计信息。
    """
    ensure_data_files()
    with USER_STATS_PATH.open("w", encoding="utf-8") as file:
        json.dump(stats, file, ensure_ascii=False, indent=2)


def load_rewards():
    """
    读取奖励列表。

    Returns:
        pandas.DataFrame: rewards.csv 对应数据。
    """
    ensure_data_files()
    rewards_df = pd.read_csv(REWARDS_PATH, encoding="utf-8-sig")
    for col in REWARD_COLUMNS:
        if col not in rewards_df.columns:
            rewards_df[col] = ""
    rewards_df = rewards_df[REWARD_COLUMNS]
    rewards_df["reward_id"] = pd.to_numeric(rewards_df["reward_id"], errors="coerce")
    rewards_df["cost"] = pd.to_numeric(rewards_df["cost"], errors="coerce")
    rewards_df["reward_name"] = rewards_df["reward_name"].fillna("").astype(str)
    rewards_df["description"] = rewards_df["description"].fillna("").astype(str)
    return rewards_df


def load_redemption_records():
    """
    读取兑换记录。

    Returns:
        pandas.DataFrame: redemption_records.csv 对应数据。
    """
    ensure_data_files()
    df = pd.read_csv(REDEMPTION_PATH, encoding="utf-8-sig")
    return _normalize_redemption_df(df)


def redeem_reward(reward_id):
    """
    兑换奖励。

    Args:
        reward_id: 奖励 ID。

    Returns:
        dict: 兑换结果。
    """
    rewards_df = load_rewards()
    matched = rewards_df[rewards_df["reward_id"].astype(str) == str(reward_id)]
    if matched.empty:
        return {"success": False, "message": "奖励不存在"}

    reward = matched.iloc[0]
    cost = int(float(reward["cost"]))

    stats = load_user_stats()
    current_points = int(stats.get("current_points", 0))
    if current_points < cost:
        return {"success": False, "message": "积分不足"}

    stats["current_points"] = current_points - cost
    save_user_stats(stats)

    redemption_df = load_redemption_records()
    record_id = _next_id(redemption_df, "record_id")
    new_record = {
        "record_id": record_id,
        "reward_name": reward["reward_name"],
        "cost": cost,
        "redeemed_at": _now_str(),
    }
    redemption_df = pd.concat([redemption_df, pd.DataFrame([new_record])], ignore_index=True)
    _save_redemption_records(redemption_df)

    return {"success": True, "message": "兑换成功"}


if __name__ == "__main__":
    print("开始 storage.py 自检...")
    ensure_data_files()
    print("数据文件检查完成。")

    sample_task = {
        "task_name": "机器学习课程报告",
        "tag": "学习",
        "task_type": "报告",
        "deadline": (date.today() + timedelta(days=1)).isoformat(),
        "estimated_hours": 4.5,
        "difficulty": 5,
        "importance": 5,
        "note": "需要整合实验结果并完成结论部分",
    }
    added_task = add_task(sample_task)
    print(f"新增任务成功: {added_task}")

    sample_event = {
        "event_name": "线性代数课程",
        "event_type": "课程",
        "date": (date.today() + timedelta(days=1)).isoformat(),
        "start_time": "09:00",
        "end_time": "10:30",
        "note": "按时到教室",
    }
    added_events = add_event(sample_event)
    print(f"新增固定安排成功: {added_events}")

    completed_task = complete_task(added_task["task_id"], actual_hours=4.0)
    print(f"任务完成成功: {completed_task}")

    redemption_result = redeem_reward(1)
    print(f"奖励兑换结果: {redemption_result}")
    print(f"当前用户统计: {load_user_stats()}")

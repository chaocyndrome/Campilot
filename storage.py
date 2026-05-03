"""Campilot 数据读写与业务逻辑层。"""

import json
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
    "tag",
    "date",
    "start_time",
    "end_time",
    "event_type",
    "note",
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


def _normalize_events_df(df):
    """标准化固定安排表结构与字段类型。"""
    normalized = df.copy()
    for col in EVENT_COLUMNS:
        if col not in normalized.columns:
            normalized[col] = ""
    normalized = normalized[EVENT_COLUMNS]

    normalized["event_id"] = pd.to_numeric(normalized["event_id"], errors="coerce")
    for col in ["event_name", "tag", "date", "start_time", "end_time", "event_type", "note"]:
        normalized[col] = normalized[col].fillna("").astype(str)

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
    return _normalize_tasks_df(df)


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
    return _normalize_events_df(df)


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
        event_data (dict): 包含 event_name, tag, date, start_time, end_time,
            event_type, note。

    Returns:
        dict: 新增后的固定安排字典。
    """
    events_df = load_events()
    event_id = _next_id(events_df, "event_id")

    new_event = {
        "event_id": event_id,
        "event_name": event_data.get("event_name", ""),
        "tag": event_data.get("tag", ""),
        "date": str(event_data.get("date", "")),
        "start_time": str(event_data.get("start_time", "")),
        "end_time": str(event_data.get("end_time", "")),
        "event_type": event_data.get("event_type", ""),
        "note": event_data.get("note", ""),
    }

    events_df = pd.concat([events_df, pd.DataFrame([new_event])], ignore_index=True)
    save_events(events_df)
    return new_event


def delete_event(event_id):
    """
    删除固定安排。

    Args:
        event_id: 固定安排 ID。

    Returns:
        bool: 是否删除成功。
    """
    events_df = load_events()
    original_count = len(events_df)
    events_df = events_df[events_df["event_id"].astype(str) != str(event_id)].copy()

    if len(events_df) == original_count:
        return False

    save_events(events_df)
    return True


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
        "tag": "课程",
        "date": (date.today() + timedelta(days=1)).isoformat(),
        "start_time": "09:00",
        "end_time": "10:30",
        "event_type": "上课",
        "note": "按时到教室",
    }
    added_event = add_event(sample_event)
    print(f"新增固定安排成功: {added_event}")

    completed_task = complete_task(added_task["task_id"], actual_hours=4.0)
    print(f"任务完成成功: {completed_task}")

    redemption_result = redeem_reward(1)
    print(f"奖励兑换结果: {redemption_result}")
    print(f"当前用户统计: {load_user_stats()}")

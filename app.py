"""Campilot Flask 界面骨架应用。"""

from datetime import date, datetime, timedelta

from flask import Flask, flash, redirect, render_template, request, url_for

import storage


app = Flask(__name__)
app.secret_key = "campilot-dev-secret-key"
storage.ensure_data_files()


def _load_page_data():
    """统一读取页面所需数据。"""
    tasks_df = storage.load_tasks()
    events_df = storage.load_events()
    stats = storage.load_user_stats()
    rewards_df = storage.load_rewards()
    records_df = storage.load_redemption_records()

    tasks = tasks_df.fillna("").to_dict(orient="records")
    events = events_df.fillna("").to_dict(orient="records")
    rewards = rewards_df.fillna("").to_dict(orient="records")
    records = records_df.fillna("").to_dict(orient="records")

    return {
        "tasks": tasks,
        "events": events,
        "stats": stats,
        "rewards": rewards,
        "records": records,
    }


def _safe_days_left(value, default=9999):
    """将 days_left 转为可排序数值。"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_number(value, default=0):
    """将输入安全转为数值。"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _priority_rank(priority):
    """优先级排序映射：高 > 中 > 低。"""
    rank_map = {"高": 0, "中": 1, "低": 2}
    return rank_map.get(str(priority), 3)


def _parse_date(value):
    """解析 YYYY-MM-DD 字符串为 date。"""
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _parse_time(value):
    """解析 HH:MM 或 HH:MM:SS 字符串为 datetime.time。"""
    text = str(value).strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    return None


def _event_hours(start_time, end_time):
    """计算单条固定安排时长（小时）。"""
    start = _parse_time(start_time)
    end = _parse_time(end_time)
    if start is None or end is None:
        return 0.0

    start_minutes = start.hour * 60 + start.minute + start.second / 60
    end_minutes = end.hour * 60 + end.minute + end.second / 60
    if end_minutes <= start_minutes:
        return 0.0
    return (end_minutes - start_minutes) / 60


def _daily_status(total_hours, _ddl_count=None):
    """根据固定安排总时长计算当日状态。"""
    if total_hours >= 5:
        return "较忙"
    if 2 <= total_hours < 5:
        return "适中"
    return "较空"


def _redirect_back(default_endpoint="today"):
    """优先返回来源页面，否则回退到默认路由。"""
    next_url = request.form.get("next")
    if next_url:
        return redirect(next_url)
    if request.referrer:
        return redirect(request.referrer)
    return redirect(url_for(default_endpoint))


@app.route("/")
def index():
    """首页重定向到今日任务页。"""
    return redirect(url_for("today"))


@app.route("/today")
def today():
    """今日任务页。"""
    context = _load_page_data()

    unfinished_tasks = [task for task in context["tasks"] if task.get("status") != "已完成"]
    recommendable_tasks = [
        task for task in unfinished_tasks if task.get("status") != "今日关注"
    ]
    recommended_tasks = sorted(
        recommendable_tasks,
        key=lambda task: (
            _priority_rank(task.get("priority")),
            _safe_days_left(task.get("days_left")),
            -_safe_number(task.get("estimated_hours")),
            -_safe_number(task.get("importance")),
        ),
    )[:5]

    focus_tasks = [task for task in unfinished_tasks if task.get("status") == "今日关注"]

    recent_ddl = [
        task
        for task in unfinished_tasks
        if 0 <= _safe_days_left(task.get("days_left"), default=-1) <= 7
    ]
    recent_ddl = sorted(recent_ddl, key=lambda task: _safe_days_left(task.get("days_left")))

    unfinished_tasks_sorted = sorted(
        unfinished_tasks,
        key=lambda task: (
            _safe_days_left(task.get("days_left")),
            _priority_rank(task.get("priority")),
        ),
    )

    context.update(
        {
            "active_page": "today",
            "unfinished_tasks": unfinished_tasks_sorted,
            "recommended_tasks": recommended_tasks,
            "focus_tasks": focus_tasks,
            "recent_ddl": recent_ddl,
        }
    )
    return render_template("today.html", **context)


@app.route("/timeline")
def timeline():
    """本周时间线页。"""
    context = _load_page_data()

    unfinished_tasks = [task for task in context["tasks"] if task.get("status") != "已完成"]
    weekday_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    today_date = date.today()

    timeline_days = []
    for offset in range(7):
        current_day = today_date + timedelta(days=offset)
        current_day_str = current_day.isoformat()

        day_events = [
            event
            for event in context["events"]
            if str(event.get("date", "")).strip() == current_day_str
        ]
        day_events_sorted = sorted(
            day_events,
            key=lambda event: (
                _parse_time(event.get("start_time")) is None,
                _parse_time(event.get("start_time")) or datetime.max.time(),
            ),
        )
        fixed_event_lines = [
            (
                f"{event.get('start_time', '')}-{event.get('end_time', '')} "
                f"[{event.get('event_type', '其他') or '其他'}] {event.get('event_name', '')}"
            )
            for event in day_events_sorted
        ]

        ddl_tasks = []
        recommended_tasks = []
        for task in unfinished_tasks:
            deadline_date = _parse_date(task.get("deadline"))
            if deadline_date is None:
                continue
            # 已过 DDL 的任务不在该日期列中展示（含推荐关注）。
            if deadline_date < current_day:
                continue

            if deadline_date == current_day:
                ddl_tasks.append(task)

            days_to_deadline = (deadline_date - current_day).days
            priority = str(task.get("priority", ""))

            should_recommend = False
            if priority == "高" and days_to_deadline <= 3:
                should_recommend = True
            elif priority == "中" and days_to_deadline <= 2:
                should_recommend = True
            elif priority == "低" and deadline_date == current_day:
                should_recommend = True

            if should_recommend:
                task_for_display = dict(task)
                task_for_display["days_to_deadline"] = days_to_deadline
                recommended_tasks.append(task_for_display)

        ddl_tasks = sorted(
            ddl_tasks,
            key=lambda task: (
                _priority_rank(task.get("priority")),
                _safe_number(task.get("estimated_hours")),
            ),
        )
        recommended_tasks = sorted(
            recommended_tasks,
            key=lambda task: (
                _priority_rank(task.get("priority")),
                task.get("days_to_deadline", 9999),
            ),
        )

        total_event_hours = sum(
            _event_hours(event.get("start_time"), event.get("end_time"))
            for event in day_events_sorted
        )
        ddl_count = len(ddl_tasks)
        day_status = _daily_status(total_event_hours, ddl_count)

        timeline_days.append(
            {
                "date_str": current_day_str,
                "weekday": weekday_names[current_day.weekday()],
                "fixed_event_lines": fixed_event_lines,
                "ddl_tasks": ddl_tasks,
                "recommended_tasks": recommended_tasks,
                "status": day_status,
                "total_event_hours": round(total_event_hours, 1),
                "ddl_count": ddl_count,
            }
        )

    context.update(
        {
            "active_page": "timeline",
            "timeline_days": timeline_days,
        }
    )
    return render_template("timeline.html", **context)


@app.route("/manage")
def manage():
    """添加 / 管理页。"""
    context = _load_page_data()
    show_mode = request.args.get("show", "active").strip().lower()
    if show_mode not in {"active", "all"}:
        show_mode = "active"

    all_tasks = context["tasks"]
    tag_options = sorted(
        {
            str(task.get("tag", "")).strip()
            for task in all_tasks
            if str(task.get("tag", "")).strip()
        }
    )
    tasks = all_tasks
    if show_mode == "active":
        tasks = [task for task in tasks if task.get("status") != "已完成"]

    context.update(
        {
            "active_page": "manage",
            "tasks": tasks,
            "task_tag_options": tag_options,
            "show_mode": show_mode,
            "show_label": "显示未完成" if show_mode == "active" else "显示所有",
            "manage_next_url": url_for("manage", show=show_mode),
        }
    )
    return render_template("manage.html", **context)


@app.route("/tasks/add", methods=["POST"])
def add_task():
    """处理任务新增请求。"""
    task_data = {
        "task_name": request.form.get("task_name", "").strip(),
        "tag": request.form.get("tag", "").strip(),
        "task_type": request.form.get("task_type", "").strip(),
        "deadline": request.form.get("deadline", "").strip(),
        "estimated_hours": request.form.get("estimated_hours", "").strip(),
        "difficulty": request.form.get("difficulty", "").strip(),
        "importance": request.form.get("importance", "").strip(),
        "note": request.form.get("note", "").strip(),
    }

    try:
        storage.add_task(task_data)
        flash("任务添加成功", "success")
    except Exception as exc:
        flash(f"任务添加失败：{exc}", "error")
    return redirect(url_for("manage"))


@app.route("/events/add", methods=["POST"])
def add_event():
    """处理固定安排新增请求。"""
    event_data = {
        "event_name": request.form.get("event_name", "").strip(),
        "event_type": request.form.get("event_type", "").strip(),
        "date": request.form.get("date", "").strip(),
        "start_time": request.form.get("start_time", "").strip(),
        "end_time": request.form.get("end_time", "").strip(),
        "note": request.form.get("note", "").strip(),
    }

    try:
        storage.add_event(event_data)
        flash("固定安排添加成功", "success")
    except Exception as exc:
        flash(f"固定安排添加失败：{exc}", "error")
    return redirect(url_for("manage"))


@app.route("/tasks/delete/<task_id>", methods=["POST"])
def delete_task(task_id):
    """删除任务。"""
    is_deleted = storage.delete_task(task_id)
    if is_deleted:
        flash("任务删除成功", "success")
    else:
        flash("任务不存在或已删除", "error")
    return _redirect_back(default_endpoint="manage")


@app.route("/tasks/update/<task_id>", methods=["POST"])
def update_task(task_id):
    """更新任务信息。"""
    tasks_df = storage.load_tasks()
    target_rows = tasks_df[tasks_df["task_id"].astype(str) == str(task_id)]
    if target_rows.empty:
        flash("任务不存在或已删除", "error")
        return _redirect_back(default_endpoint="manage")

    current = target_rows.iloc[0]
    updated_data = {
        "task_name": request.form.get("task_name", "").strip(),
        "tag": request.form.get("tag", "").strip(),
        "task_type": request.form.get("task_type", "").strip(),
        "deadline": request.form.get("deadline", "").strip(),
        "estimated_hours": request.form.get("estimated_hours", "").strip(),
        "difficulty": request.form.get("difficulty", "").strip(),
        "importance": request.form.get("importance", "").strip(),
        "status": request.form.get("status", "").strip(),
        "note": request.form.get("note", "").strip(),
    }

    try:
        recalculate_priority = (
            str(updated_data["deadline"]) != str(current.get("deadline", ""))
            or float(updated_data["estimated_hours"]) != float(current.get("estimated_hours", 0))
            or int(updated_data["difficulty"]) != int(float(current.get("difficulty", 0)))
            or int(updated_data["importance"]) != int(float(current.get("importance", 0)))
            or str(updated_data["task_type"]) != str(current.get("task_type", ""))
        )
        storage.update_task(
            task_id=task_id,
            updated_data=updated_data,
            recalculate_priority=recalculate_priority,
        )
        flash("任务已更新", "success")
    except Exception as exc:
        flash(f"任务更新失败：{exc}", "error")
    return _redirect_back(default_endpoint="manage")


@app.route("/tasks/focus/<task_id>", methods=["POST"])
def focus_task(task_id):
    """将任务加入今日关注。"""
    try:
        storage.update_task_status(task_id, "今日关注")
        flash("已加入今日关注", "success")
    except Exception as exc:
        flash(f"加入今日关注失败：{exc}", "error")
    return _redirect_back(default_endpoint="today")


@app.route("/tasks/complete/<task_id>", methods=["POST"])
def complete_task(task_id):
    """完成任务并提示积分。"""
    try:
        completed_task = storage.complete_task(task_id)
        points = int(float(completed_task.get("points", 0)))
        flash(f"任务已完成，获得 {points} 积分", "success")
    except Exception as exc:
        flash(f"完成任务失败：{exc}", "error")
    return _redirect_back(default_endpoint="today")


@app.route("/events/delete/<event_id>", methods=["POST"])
def delete_event(event_id):
    """删除固定安排。"""
    is_deleted = storage.delete_event(event_id)
    if is_deleted:
        flash("固定安排删除成功", "success")
    else:
        flash("固定安排不存在或已删除", "error")
    return _redirect_back(default_endpoint="manage")


@app.route("/rewards")
def rewards():
    """奖励 / 成就页。"""
    context = _load_page_data()

    tasks = context["tasks"]
    stats = context["stats"]
    today_date = date.today()
    ddl_window_end = today_date + timedelta(days=6)

    completed_tasks_count = sum(1 for task in tasks if task.get("status") == "已完成")
    unfinished_tasks_count = sum(1 for task in tasks if task.get("status") != "已完成")
    completed_high_priority_count = sum(
        1
        for task in tasks
        if task.get("status") == "已完成" and str(task.get("priority", "")) == "高"
    )

    priority_counts = {"高": 0, "中": 0, "低": 0}
    for task in tasks:
        priority = str(task.get("priority", ""))
        if priority in priority_counts:
            priority_counts[priority] += 1

    tag_counts = {}
    for task in tasks:
        tag = str(task.get("tag", "")).strip() or "未分类"
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    sorted_tag_counts = sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))

    future_ddl_count = 0
    for task in tasks:
        if task.get("status") == "已完成":
            continue
        deadline = _parse_date(task.get("deadline"))
        if deadline is None:
            continue
        if today_date <= deadline <= ddl_window_end:
            future_ddl_count += 1

    achievements = [
        {"name": "初次完成", "unlocked": completed_tasks_count >= 1},
        {"name": "稳定推进", "unlocked": completed_tasks_count >= 5},
        {"name": "任务达人", "unlocked": completed_tasks_count >= 10},
        {"name": "积分充足", "unlocked": int(stats.get("total_points", 0)) >= 500},
        {"name": "高优先级处理者", "unlocked": completed_high_priority_count >= 3},
    ]

    records_sorted = sorted(
        context["records"],
        key=lambda record: str(record.get("redeemed_at", "")),
        reverse=True,
    )

    context.update(
        {
            "active_page": "rewards",
            "records": records_sorted,
            "achievements": achievements,
            "stats_completed_tasks": completed_tasks_count,
            "stats_unfinished_tasks": unfinished_tasks_count,
            "priority_counts": priority_counts,
            "tag_counts": sorted_tag_counts,
            "future_ddl_count": future_ddl_count,
        }
    )
    return render_template("rewards.html", **context)


@app.route("/rewards/redeem/<reward_id>", methods=["POST"])
def redeem_reward(reward_id):
    """兑换奖励。"""
    result = storage.redeem_reward(reward_id)
    flash(result.get("message", "兑换失败"), "success" if result.get("success") else "error")
    return redirect(url_for("rewards"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

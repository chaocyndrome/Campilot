"""Campilot Flask 界面骨架应用。"""

from datetime import date

from flask import Flask, redirect, render_template, url_for

import storage


app = Flask(__name__)
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


@app.route("/")
def index():
    """首页重定向到今日任务页。"""
    return redirect(url_for("today"))


@app.route("/today")
def today():
    """今日任务页。"""
    context = _load_page_data()

    unfinished_tasks = [task for task in context["tasks"] if task.get("status") != "已完成"]
    recommended_tasks = [task for task in unfinished_tasks if task.get("priority") == "高"][:5]
    focus_tasks = [task for task in unfinished_tasks if task.get("priority") == "中"][:5]
    recent_ddl = sorted(unfinished_tasks, key=lambda t: _safe_days_left(t.get("days_left")))[:5]

    context.update(
        {
            "active_page": "today",
            "unfinished_tasks": unfinished_tasks,
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

    events_by_date = {}
    for event in context["events"]:
        event_date = event.get("date") or "未设置日期"
        events_by_date.setdefault(event_date, []).append(event)

    unfinished_tasks = [task for task in context["tasks"] if task.get("status") != "已完成"]
    today_ddl = [task for task in unfinished_tasks if _safe_days_left(task.get("days_left")) == 0]
    suggested_tasks = [task for task in unfinished_tasks if task.get("priority") in {"高", "中"}][:5]

    completed_today = 0
    for task in context["tasks"]:
        completed_at = str(task.get("completed_at", ""))
        if task.get("status") == "已完成" and completed_at.startswith(date.today().isoformat()):
            completed_today += 1

    context.update(
        {
            "active_page": "timeline",
            "events_by_date": dict(sorted(events_by_date.items(), key=lambda item: item[0])),
            "today_ddl": today_ddl,
            "suggested_tasks": suggested_tasks,
            "completed_today": completed_today,
        }
    )
    return render_template("timeline.html", **context)


@app.route("/manage")
def manage():
    """添加 / 管理页。"""
    context = _load_page_data()
    context.update({"active_page": "manage"})
    return render_template("manage.html", **context)


@app.route("/rewards")
def rewards():
    """奖励 / 成就页。"""
    context = _load_page_data()
    context.update({"active_page": "rewards"})
    return render_template("rewards.html", **context)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

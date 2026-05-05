import os
import random

import pandas as pd


def _get_priority(days_left, estimated_hours, difficulty, importance):
    is_high = (
        (days_left <= 1)
        or (days_left <= 3 and estimated_hours >= 3)
        or (days_left <= 5 and difficulty >= 4)
        or (importance >= 5 and days_left <= 5)
    )

    is_low = (
        (days_left >= 7 and difficulty <= 2 and estimated_hours <= 1.5)
        or (importance <= 2 and days_left >= 5)
    )

    if is_high:
        return "高"
    if is_low:
        return "低"
    return "中"


def create_sample_dataset(
    csv_path="data/task_priority_dataset.csv", n_samples=300, random_state=42
):
    random.seed(random_state)

    task_types = ["作业", "实验", "预习", "复习", "报告", "项目", "事务"]
    records = []

    for _ in range(n_samples):
        days_left = random.randint(0, 14)
        estimated_hours = round(random.uniform(0.5, 8.0), 1)
        difficulty = random.randint(1, 5)
        importance = random.randint(1, 5)
        task_type = random.choice(task_types)

        priority = _get_priority(days_left, estimated_hours, difficulty, importance)

        records.append(
            {
                "days_left": days_left,
                "estimated_hours": estimated_hours,
                "difficulty": difficulty,
                "importance": importance,
                "task_type": task_type,
                "priority": priority,
            }
        )

    df = pd.DataFrame(records)

    output_dir = os.path.dirname(csv_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    return df


if __name__ == "__main__":
    output_path = "data/task_priority_dataset.csv"
    dataset = create_sample_dataset(csv_path=output_path, n_samples=300, random_state=42)

    print(f"数据已保存到: {output_path}")
    print("\n数据前 5 行:")
    print(dataset.head())

    print("\npriority 各类别数量:")
    print(dataset["priority"].value_counts())

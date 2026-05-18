import os
import random

import pandas as pd

from priority import grade_priority


def _get_priority(days_left, estimated_hours, difficulty, importance, task_type="事务"):
    return grade_priority(
        {
            "days_left": days_left,
            "estimated_hours": estimated_hours,
            "difficulty": difficulty,
            "importance": importance,
            "task_type": task_type,
        }
    )


def create_sample_dataset(
    csv_path="data/task_priority_dataset.csv", n_samples=300, random_state=42
):
    random.seed(random_state)

    task_types = ["作业", "实验", "预习", "复习", "报告", "项目", "事务", "阅读"]
    records = []

    for _ in range(n_samples):
        days_left = random.randint(0, 14)
        estimated_hours = round(random.uniform(0.5, 8.0), 1)
        difficulty = random.randint(1, 5)
        importance = random.randint(1, 5)
        task_type = random.choice(task_types)

        priority = grade_priority(
            {
                "days_left": days_left,
                "estimated_hours": estimated_hours,
                "difficulty": difficulty,
                "importance": importance,
                "task_type": task_type,
            }
        )

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

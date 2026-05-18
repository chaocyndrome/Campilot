from model import train_priority_model, predict_priority


def run_manual_tests():
    model, metrics = train_priority_model()

    test_tasks = [
        {
            "name": "当天截止的小作业",
            "expected": "高",
            "data": {
                "days_left": 0,
                "estimated_hours": 1,
                "difficulty": 2,
                "importance": 3,
                "task_type": "作业"
            }
        },
        {
            "name": "很远且很简单的阅读",
            "expected": "低",
            "data": {
                "days_left": 10,
                "estimated_hours": 0.5,
                "difficulty": 1,
                "importance": 1,
                "task_type": "预习"
            }
        },
        {
            "name": "快截止且耗时长的重要报告",
            "expected": "特急",
            "data": {
                "days_left": 2,
                "estimated_hours": 5,
                "difficulty": 4,
                "importance": 5,
                "task_type": "报告"
            }
        },
        {
            "name": "一周后截止的中等复习任务",
            "expected": "中",
            "data": {
                "days_left": 7,
                "estimated_hours": 2,
                "difficulty": 3,
                "importance": 3,
                "task_type": "复习"
            }
        },
        {
            "name": "重要但不算紧急的项目任务",
            "expected": "较高",
            "data": {
                "days_left": 6,
                "estimated_hours": 4,
                "difficulty": 3,
                "importance": 5,
                "task_type": "项目"
            }
        }
    ]

    print("===== Campilot 手动样例测试 =====")

    for item in test_tasks:
        result = predict_priority(item["data"], model=model)

        print()
        print(f"测试样例：{item['name']}")
        print(f"输入数据：{item['data']}")
        print(f"预期优先级：{item['expected']}")
        print(f"模型预测：{result['priority']}")
        print(f"推荐理由：{result['reason']}")

        if result["priority"] == item["expected"]:
            print("结果：符合预期")
        else:
            print("结果：与预期不一致，需要检查")


if __name__ == "__main__":
    run_manual_tests()

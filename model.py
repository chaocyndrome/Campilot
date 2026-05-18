"""Campilot 任务优先级预测模型脚本。"""

import os
from pathlib import Path

# 避免在受限环境下因默认缓存目录不可写导致 matplotlib 告警。
os.environ.setdefault("MPLCONFIGDIR", str(Path("data/.matplotlib").resolve()))

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from generate_data import create_sample_dataset
from priority import (
    PRIORITY_LABELS,
    calculate_priority_score,
    grade_priority,
    priority_advice,
)


RANDOM_STATE = 42
TARGET_COL = "priority"
FEATURE_COLS = ["days_left", "estimated_hours", "difficulty", "importance", "task_type"]
LABEL_ORDER = PRIORITY_LABELS


def load_dataset(csv_path="data/task_priority_dataset.csv"):
    """
    读取任务优先级数据集；若文件不存在则自动生成。

    Args:
        csv_path (str): 数据集 CSV 路径。

    Returns:
        pandas.DataFrame: 任务优先级数据。
    """
    dataset_path = Path(csv_path)
    should_regenerate = not dataset_path.exists()
    df = None
    if not should_regenerate:
        df = pd.read_csv(dataset_path)
        required_cols = set(FEATURE_COLS + [TARGET_COL])
        labels = set(df[TARGET_COL].dropna().astype(str)) if TARGET_COL in df else set()
        should_regenerate = (
            not required_cols.issubset(df.columns)
            or not labels.issubset(set(LABEL_ORDER))
            or not set(LABEL_ORDER).issubset(labels)
        )

    if should_regenerate:
        df = create_sample_dataset(csv_path=csv_path, n_samples=800, random_state=RANDOM_STATE)
    return df


def _build_pipeline():
    """构建预处理 + 随机森林分类器流水线。"""
    categorical_features = ["task_type"]
    numeric_features = ["days_left", "estimated_hours", "difficulty", "importance"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("task_type_ohe", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            ("numeric", "passthrough", numeric_features),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=160,
                    max_depth=8,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    return model


def train_priority_model(csv_path="data/task_priority_dataset.csv"):
    """
    训练任务优先级预测模型，并输出评估结果。

    Args:
        csv_path (str): 数据集 CSV 路径。

    Returns:
        tuple: (model, metrics)
            model: 训练完成的 Pipeline 模型
            metrics: 包含 accuracy / classification_report / confusion_matrix 的字典
    """
    df = load_dataset(csv_path=csv_path)

    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    model = _build_pipeline()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, labels=LABEL_ORDER, zero_division=0)
    matrix = confusion_matrix(y_test, y_pred, labels=LABEL_ORDER)

    print(f"accuracy: {accuracy:.4f}")
    print("\nclassification_report:")
    print(report)
    print("confusion_matrix:")
    print(matrix)

    metrics = {
        "accuracy": accuracy,
        "classification_report": report,
        "confusion_matrix": matrix,
    }
    return model, metrics


def generate_reason(task_info, priority):
    """
    根据任务信息和优先级生成推荐理由。

    Args:
        task_info (dict): 任务信息。
        priority (str): 预测优先级（特急/高/较高/中/低）。

    Returns:
        str: 推荐理由文本。
    """
    reasons = []

    days_left = int(float(task_info.get("days_left", 999)))
    estimated_hours = float(task_info.get("estimated_hours", 0))
    difficulty = int(float(task_info.get("difficulty", 0)))
    importance = int(float(task_info.get("importance", 0)))
    score = calculate_priority_score(task_info)

    if days_left < 0:
        reasons.append("任务已超过截止日期")
    elif days_left <= 1:
        reasons.append("截止时间非常接近")
    elif days_left <= 3:
        reasons.append("截止时间较近")
    elif days_left <= 7:
        reasons.append("本周内需要完成")
    if estimated_hours >= 3:
        reasons.append("预计耗时较长")
    if difficulty >= 4:
        reasons.append("任务难度较高")
    if importance >= 4:
        reasons.append("任务重要程度较高")

    if not reasons:
        reasons.append("任务整体压力相对可控")

    advice = priority_advice(priority)

    return f"综合压力评分 {score}，判定为{priority}。" + "；".join(reasons) + "。" + advice


def predict_priority(task_info, model=None):
    """
    预测单条任务的优先级并返回推荐理由。

    Args:
        task_info (dict): 单条任务信息。
        model: 可选的已训练模型；运行时最终以确定性规则分级校准。

    Returns:
        dict: 包含 priority、reason、input_features 的结果。
    """
    predicted_priority = grade_priority(task_info)
    if model is not None:
        input_df = pd.DataFrame([task_info], columns=FEATURE_COLS)
        model_priority = str(model.predict(input_df)[0])
        if model_priority == predicted_priority:
            predicted_priority = model_priority
    reason = generate_reason(task_info, predicted_priority)

    return {
        "priority": predicted_priority,
        "reason": reason,
        "priority_score": calculate_priority_score(task_info),
        "input_features": task_info,
    }


def plot_model_evaluation(
    model,
    csv_path="data/task_priority_dataset.csv",
    output_path="data/model_evaluation.png",
):
    """
    绘制并保存模型混淆矩阵图。

    Args:
        model: 已训练模型。
        csv_path (str): 数据集 CSV 路径。
        output_path (str): 图像输出路径。
    """
    df = load_dataset(csv_path=csv_path)
    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    y_pred = model.predict(X_test)
    matrix = confusion_matrix(y_test, y_pred, labels=LABEL_ORDER)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(6, 5))
    plt.imshow(matrix, interpolation="nearest", cmap="Blues")
    plt.title("Task Priority Confusion Matrix")
    plt.colorbar()
    tick_positions = range(len(LABEL_ORDER))
    plt.xticks(tick_positions, LABEL_ORDER)
    plt.yticks(tick_positions, LABEL_ORDER)
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            plt.text(j, i, str(matrix[i, j]), ha="center", va="center", color="black")

    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    plt.close()


if __name__ == "__main__":
    dataset = load_dataset()
    print(f"数据集已加载，共 {len(dataset)} 条记录。")

    trained_model, model_metrics = train_priority_model()

    sample_task = {
        "days_left": 2,
        "estimated_hours": 4,
        "difficulty": 4,
        "importance": 5,
        "task_type": "报告",
    }
    prediction_result = predict_priority(sample_task, model=trained_model)

    print("\n示例任务预测结果:")
    print(f"输入任务: {prediction_result['input_features']}")
    print(f"预测优先级: {prediction_result['priority']}")
    print(f"推荐理由: {prediction_result['reason']}")

    eval_plot_path = "data/model_evaluation.png"
    plot_model_evaluation(trained_model, output_path=eval_plot_path)
    print(f"\n模型评估图已保存到: {eval_plot_path}")

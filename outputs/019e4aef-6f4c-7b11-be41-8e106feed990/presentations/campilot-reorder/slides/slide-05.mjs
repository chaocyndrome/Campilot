import { addBackground, addKicker, addTitle, addFooter, addBodyText, addPanel, addStep, addMetric, C } from "./theme.mjs";

export async function slide05(presentation, ctx) {
  const slide = presentation.slides.add();
  addBackground(slide, ctx);
  addKicker(slide, ctx, "IMPLEMENTATION", 70, 44, C.amber);
  addTitle(slide, ctx, "具体实现方式：预测、解释与反馈写进同一条数据链", "AI 模块不是单独展示结果，而是进入新增、刷新、推荐和完成任务的实际流程。");

  const steps = [
    ["01", "任务表单", "DDL / 耗时 / 难度 / 重要度 / 类型"],
    ["02", "预测函数", "predict_priority"],
    ["03", "解释规则", "压力评分 + 原因文本"],
    ["04", "页面推荐", "今日关注 + 时间线窗口"],
    ["05", "完成反馈", "积分 + 成就 + 统计"],
  ];
  steps.forEach(([num, title, note], i) => {
    const x = 84 + i * 218;
    addStep(slide, ctx, num, title, note, x, 238, 176, i === 1 || i === 2);
    if (i < 4) addBodyText(slide, ctx, "→", x + 178, 280, 40, 28, { fontSize: 24, color: C.cyan, align: "center" });
  });

  addPanel(slide, ctx, 90, 420, 298, 116, "#101B2E", "#334155");
  addBodyText(slide, ctx, "模型训练", 116, 442, 120, 24, { fontSize: 20, bold: true, color: C.cyan });
  addBodyText(slide, ctx, "model.py 使用 Pipeline、OneHotEncoder、RandomForestClassifier；数据集 800 条。", 116, 478, 232, 42, { fontSize: 16, color: C.text });

  addPanel(slide, ctx, 430, 420, 298, 116, "#101B2E", "#334155");
  addBodyText(slide, ctx, "可解释校准", 456, 442, 130, 24, { fontSize: 20, bold: true, color: C.violet });
  addBodyText(slide, ctx, "priority.py 计算压力评分，并把截止时间、耗时、难度等转成推荐理由。", 456, 478, 232, 42, { fontSize: 16, color: C.text });

  addPanel(slide, ctx, 770, 420, 298, 116, "#101B2E", "#334155");
  addBodyText(slide, ctx, "业务闭环", 796, 442, 120, 24, { fontSize: 20, bold: true, color: C.amber });
  addBodyText(slide, ctx, "storage.py 保存任务状态，完成后计算积分并更新 user_stats.json。", 796, 478, 232, 42, { fontSize: 16, color: C.text });

  addMetric(slide, ctx, "0.88", "模型测试准确率", 90, 568, 150, C.cyan);
  addMetric(slide, ctx, "5级", "优先级体系", 264, 568, 150, C.violet);
  addMetric(slide, ctx, "2015", "累计积分样例", 438, 568, 150, C.amber);

  addFooter(slide, ctx, 5, "Source: model.py, priority.py, storage.py, app.py, data/user_stats.json");
  slide.speakerNotes.setText("最后补技术实现：新增任务时构造特征，调用预测函数得到优先级和原因；页面再按优先级、DDL、耗时排序推荐。完成任务后 storage.py 计算积分，更新统计，让 AI 判断和激励反馈接到同一条数据链上。预计 30 秒。");
  return slide;
}

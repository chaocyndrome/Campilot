import { addBackground, addKicker, addTitle, addFooter, addBodyText, addPanel, C } from "./theme.mjs";

export async function slide03(presentation, ctx) {
  const slide = presentation.slides.add();
  addBackground(slide, ctx);
  addKicker(slide, ctx, "DESIGN THINKING", 70, 44, C.violet);
  addTitle(slide, ctx, "设计思路：让 AI 提醒关注，而不是替用户排满", "项目核心是任务录入、优先级预测、建议展示、完成反馈和积分激励。");

  const pains = [
    ["任务来源分散", "课程、作业、实验、项目混在一起"],
    ["DDL 不统一", "临近截止时才发现压力堆积"],
    ["优先级难判断", "耗时、难度、重要程度很难同时比较"],
  ];
  const principles = [
    ["轻量输入", "尽量少填，但保留关键特征"],
    ["可解释推荐", "不仅给等级，也说明原因"],
    ["正反馈闭环", "完成任务后给积分与成就感"],
  ];

  addBodyText(slide, ctx, "学生痛点", 86, 218, 220, 34, { fontSize: 21, bold: true, color: C.amber });
  addBodyText(slide, ctx, "设计回应", 744, 218, 260, 34, { fontSize: 21, bold: true, color: C.cyan });

  pains.forEach(([title, note], i) => {
    const y = 270 + i * 96;
    addPanel(slide, ctx, 86, y, 398, 66, "#101B2E", "#334155");
    addBodyText(slide, ctx, title, 108, y + 12, 200, 24, { fontSize: 20, bold: true });
    addBodyText(slide, ctx, note, 108, y + 40, 320, 18, { fontSize: 14, color: C.muted });
  });
  principles.forEach(([title, note], i) => {
    const y = 270 + i * 96;
    addPanel(slide, ctx, 744, y, 398, 66, "#0E253B", "#266B8A");
    addBodyText(slide, ctx, title, 766, y + 12, 200, 24, { fontSize: 20, bold: true });
    addBodyText(slide, ctx, note, 766, y + 40, 326, 18, { fontSize: 14, color: C.muted });
  });

  addPanel(slide, ctx, 534, 284, 154, 210, "#0A1B33", "#1E3A5F");
  addBodyText(slide, ctx, "核心判断", 558, 310, 106, 26, { fontSize: 20, bold: true, color: C.cyan, align: "center" });
  addBodyText(slide, ctx, "谁更急？\n为什么？\n做完后如何继续？", 558, 356, 106, 94, { fontSize: 22, bold: true, align: "center" });
  addBodyText(slide, ctx, "→", 494, 360, 34, 34, { fontSize: 27, color: C.violet, align: "center" });
  addBodyText(slide, ctx, "→", 696, 360, 34, 34, { fontSize: 27, color: C.cyan, align: "center" });

  addBodyText(slide, ctx, "这一页回答“为什么这个选题有价值”，具体按钮留给视频演示。", 88, 590, 760, 28, { fontSize: 17, color: "#CBD5E1" });
  addFooter(slide, ctx, 3, "Source: project routes, storage workflow, templates/manage/today/rewards");
  slide.speakerNotes.setText("这一页讲设计思路：学生的问题不是没有日历，而是任务来源分散、截止不统一、优先级难判断。所以 Campilot 的设计不是替用户排满时间，而是用 AI 提醒关注重点，并通过完成反馈形成正循环。预计 22 秒。");
  return slide;
}

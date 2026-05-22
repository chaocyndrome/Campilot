import { addBackground, addKicker, addFooter, addBodyText, addPanel, addMetric, ASSETS, C } from "./theme.mjs";

export async function slide01(presentation, ctx) {
  const slide = presentation.slides.add();
  addBackground(slide, ctx);
  addKicker(slide, ctx, "AI COURSE DEFENSE", 70, 44, C.cyan);
  await ctx.addImage(slide, { path: ASSETS.logo, x: 70, y: 80, width: 260, height: 65, fit: "contain", alt: "Campilot logo" });
  addBodyText(slide, ctx, "大学生任务管理的\n智能副驾驶", 72, 154, 520, 104, { fontSize: 41, bold: true });
  addBodyText(slide, ctx, "用优先级预测与积分激励，帮助学生识别任务风险、安排关注重点。", 74, 268, 540, 70, { fontSize: 21, color: C.muted });

  ["任务录入", "优先级预测", "今日/本周建议", "完成反馈"].forEach((step, index) => {
    const x = 76 + index * 122;
    addPanel(slide, ctx, x, 356, 104, 46, index === 1 ? "#123A63" : "#0A1B33", index === 1 ? C.cyan : "#1E3A5F");
    addBodyText(slide, ctx, step, x, 368, 104, 20, { fontSize: 15, bold: index === 1, color: index === 1 ? C.text : C.muted, align: "center" });
    if (index < 3) addBodyText(slide, ctx, "→", x + 104, 365, 18, 24, { fontSize: 20, color: C.cyan, align: "center" });
  });

  addMetric(slide, ctx, "43", "本地任务记录", 76, 450, 146, C.cyan);
  addMetric(slide, ctx, "800", "优先级样本", 244, 450, 146, C.blue);
  addMetric(slide, ctx, "2min", "PPT 开场节奏", 412, 450, 146, C.violet);

  addPanel(slide, ctx, 650, 92, 535, 367, "#081629", "#1F4B76");
  await ctx.addImage(slide, { path: ASSETS.today, x: 664, y: 106, width: 507, height: 317, fit: "cover", alt: "Campilot 今日驾驶舱截图" });
  addBodyText(slide, ctx, "真实运行页面：今日驾驶舱", 664, 434, 507, 24, { fontSize: 14, color: C.muted, align: "center" });
  addPanel(slide, ctx, 692, 502, 430, 74, "#101E39", "#2A4D75");
  addBodyText(slide, ctx, "核心定位", 716, 516, 96, 24, { fontSize: 16, bold: true, color: C.cyan });
  addBodyText(slide, ctx, "不是复杂日历，而是让学生看见“现在最该关注什么”。", 818, 516, 280, 42, { fontSize: 19 });

  addFooter(slide, ctx, 1, "Source: app.py, templates/today.html, data/*.csv, local screenshot");
  slide.speakerNotes.setText("开场先说明 Campilot：它不是复杂日历，而是帮助学生判断任务风险。这里展示的是实际运行的今日驾驶舱，后面视频会展开功能演示，PPT 只负责搭起价值和技术主线。预计 18 秒。");
  return slide;
}

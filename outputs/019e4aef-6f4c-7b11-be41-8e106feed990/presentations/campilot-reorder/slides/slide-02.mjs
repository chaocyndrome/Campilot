import { addBackground, addKicker, addTitle, addFooter, addBodyText, addPanel, addMetric, C } from "./theme.mjs";

export async function slide02(presentation, ctx) {
  const slide = presentation.slides.add();
  addBackground(slide, ctx);
  addKicker(slide, ctx, "TECH STACK", 70, 44, C.blue);
  addTitle(slide, ctx, "技术栈：轻量 Web + 本地数据 + AI 分类", "围绕课程项目目标，选择能快速交互、可解释、可本地运行的实现组合。");

  const layers = [
    ["前端页面", "HTML / CSS / JavaScript", "templates + static", C.cyan],
    ["应用服务", "Python + Flask", "路由、表单、页面上下文", C.blue],
    ["数据存储", "CSV / JSON", "任务、安排、积分、兑换记录", C.violet],
    ["AI 模块", "pandas + scikit-learn", "特征处理 + 优先级分类", C.amber],
  ];
  layers.forEach(([title, tech, note, accent], index) => {
    const y = 226 + index * 78;
    addPanel(slide, ctx, 90, y, 430, 54, "#0B1E36", "#254D70");
    ctx.addShape(slide, { x: 112, y: y + 22, width: 8, height: 8, fill: accent, line: ctx.line("#00000000", 0) });
    addBodyText(slide, ctx, title, 132, y + 10, 120, 20, { fontSize: 17, bold: true, color: C.text });
    addBodyText(slide, ctx, tech, 264, y + 9, 200, 22, { fontSize: 18, bold: true, color: accent });
    addBodyText(slide, ctx, note, 132, y + 34, 330, 16, { fontSize: 12.5, color: C.muted });
  });

  addPanel(slide, ctx, 610, 236, 470, 122, "#101B2E", "#334155");
  addBodyText(slide, ctx, "工程取舍", 638, 258, 110, 24, { fontSize: 20, bold: true, color: C.cyan });
  addBodyText(slide, ctx, "不引入复杂账号系统或云服务；把重点放在“任务风险判断”与“完成反馈闭环”。", 638, 300, 380, 42, { fontSize: 21, bold: true });

  addMetric(slide, ctx, "Flask", "网页端可交互运行", 610, 414, 158, C.blue);
  addMetric(slide, ctx, "CSV", "本地轻量存储", 790, 414, 138, C.cyan);
  addMetric(slide, ctx, "RF", "随机森林分类器", 950, 414, 138, C.violet);

  addFooter(slide, ctx, 2, "Source: requirements.txt, app.py, storage.py, model.py");
  slide.speakerNotes.setText("第二页先讲技术栈：前端用 HTML/CSS/JS，后端 Flask，本地 CSV/JSON 存储，AI 部分是 pandas 和 scikit-learn。这里强调取舍：项目没有做很重的账号或云服务，而是把精力放在任务风险判断和反馈闭环。预计 20 秒。");
  return slide;
}

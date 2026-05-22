import { addFooter, addBodyText, C } from "./theme.mjs";

export async function slide06(presentation, ctx) {
  const slide = presentation.slides.add();
  ctx.addShape(slide, { x: 0, y: 0, width: ctx.W, height: ctx.H, fill: C.bg, line: ctx.line("#00000000", 0) });
  ctx.addShape(slide, { x: 0, y: 0, width: ctx.W, height: ctx.H, fill: "#081629", line: ctx.line("#00000000", 0) });
  ctx.addShape(slide, { x: 160, y: 164, width: 960, height: 1, fill: "#1E3A5F", line: ctx.line("#00000000", 0) });
  ctx.addShape(slide, { x: 160, y: 556, width: 960, height: 1, fill: "#1E3A5F", line: ctx.line("#00000000", 0) });
  addBodyText(slide, ctx, "Campilot 让 AI 从“模型结果”\n进入真实学习场景。", 210, 258, 860, 130, {
    fontSize: 44,
    bold: true,
    align: "center",
    color: C.text,
  });
  addBodyText(slide, ctx, "谢谢老师", 520, 428, 240, 34, { fontSize: 22, color: C.cyan, align: "center" });
  addFooter(slide, ctx, 6, "Campilot final defense closing");
  slide.speakerNotes.setText("最后用这一句收束：Campilot 让 AI 从模型结果进入真实学习场景。停顿一下，结束答辩开场。预计 8 秒。");
  return slide;
}

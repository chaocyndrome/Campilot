import { addBackground, addKicker, addTitle, addFooter, addBodyText, addPanel, addScreenshot, ASSETS, C } from "./theme.mjs";

export async function slide04(presentation, ctx) {
  const slide = presentation.slides.add();
  addBackground(slide, ctx);
  addKicker(slide, ctx, "FUNCTION DEMO", 70, 44, C.cyan);
  addTitle(slide, ctx, "功能展示：播放演示视频", "这一页作为视频入口，PPT 不展开按钮细节。");

  addPanel(slide, ctx, 88, 224, 502, 300, "#081629", "#1F4B76");
  addBodyText(slide, ctx, "在此播放展示视频", 132, 286, 414, 52, { fontSize: 42, bold: true, align: "center" });
  addBodyText(slide, ctx, "建议时长约 3 分钟", 132, 354, 414, 30, { fontSize: 22, color: C.cyan, align: "center" });
  addBodyText(slide, ctx, "演示重点：录入任务 → 查看推荐 → 本周时间线 → 完成与积分反馈", 132, 414, 414, 46, { fontSize: 19, color: C.muted, align: "center" });

  await addScreenshot(slide, ctx, ASSETS.manage, 660, 224, 156, 98, "控制中枢");
  await addScreenshot(slide, ctx, ASSETS.today, 862, 224, 156, 98, "今日驾驶舱");
  await addScreenshot(slide, ctx, ASSETS.timeline, 660, 394, 156, 98, "本周任务地图");
  await addScreenshot(slide, ctx, ASSETS.rewards, 862, 394, 156, 98, "后勤补给");
  addBodyText(slide, ctx, "1", 624, 258, 24, 24, { fontSize: 17, bold: true, color: C.cyan, align: "center" });
  addBodyText(slide, ctx, "2", 826, 258, 24, 24, { fontSize: 17, bold: true, color: C.cyan, align: "center" });
  addBodyText(slide, ctx, "3", 624, 428, 24, 24, { fontSize: 17, bold: true, color: C.cyan, align: "center" });
  addBodyText(slide, ctx, "4", 826, 428, 24, 24, { fontSize: 17, bold: true, color: C.cyan, align: "center" });

  addFooter(slide, ctx, 4, "Source: local screenshots from /manage, /today, /timeline, /rewards");
  slide.speakerNotes.setText("这一页不用讲太久，直接切入视频。建议视频顺序是控制中枢、今日驾驶舱、本周任务地图、后勤补给，正好对应任务录入、推荐、时间线和激励反馈。预计口头过渡 5 秒，视频约 3 分钟。");
  return slide;
}

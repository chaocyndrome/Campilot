export const C = {
  bg: "#071426",
  panel: "#0D1D36",
  line: "#28435F",
  text: "#F8FAFC",
  muted: "#A8B3C7",
  blue: "#3B82F6",
  cyan: "#2DD4BF",
  violet: "#8B5CF6",
  amber: "#F59E0B",
  green: "#22C55E",
};

export const ASSETS = {
  logo: "/Users/selina/coding/Campilot/outputs/019e4aef-6f4c-7b11-be41-8e106feed990/presentations/campilot-reorder/assets/image.png",
  today: "/Users/selina/coding/Campilot/outputs/019e4aef-6f4c-7b11-be41-8e106feed990/presentations/campilot-reorder/assets/image2.png",
  manage: "/Users/selina/coding/Campilot/outputs/019e4aef-6f4c-7b11-be41-8e106feed990/presentations/campilot-reorder/assets/image3.png",
  timeline: "/Users/selina/coding/Campilot/outputs/019e4aef-6f4c-7b11-be41-8e106feed990/presentations/campilot-reorder/assets/image4.png",
  rewards: "/Users/selina/coding/Campilot/outputs/019e4aef-6f4c-7b11-be41-8e106feed990/presentations/campilot-reorder/assets/image5.png",
};

export function addBackground(slide, ctx) {
  ctx.addShape(slide, { x: 0, y: 0, width: ctx.W, height: ctx.H, fill: C.bg, line: ctx.line("#00000000", 0) });
  ctx.addShape(slide, { x: 902, y: 0, width: 378, height: 720, fill: "#091B35", line: ctx.line("#00000000", 0) });
  ctx.addShape(slide, { x: 906, y: 0, width: 2, height: 720, fill: "#123A63", line: ctx.line("#00000000", 0) });
  ctx.addShape(slide, { x: 70, y: 118, width: 790, height: 1, fill: C.line, line: ctx.line("#00000000", 0) });
  ctx.addShape(slide, { x: 70, y: 666, width: 1140, height: 1, fill: "#173456", line: ctx.line("#00000000", 0) });
}

export function addKicker(slide, ctx, text, x = 70, y = 48, accent = C.cyan) {
  ctx.addShape(slide, { x, y: y + 6, width: 8, height: 8, fill: accent, line: ctx.line("#00000000", 0), name: "kicker-marker" });
  ctx.addText(slide, {
    text,
    x: x + 18,
    y,
    width: 360,
    height: 22,
    fontSize: 13,
    bold: true,
    color: accent,
    typeface: "Aptos",
    valign: "middle",
    name: "kicker-label",
  });
}

export function addTitle(slide, ctx, title, subtitle) {
  ctx.addText(slide, {
    text: title,
    x: 70,
    y: 76,
    width: 840,
    height: 58,
    fontSize: 36,
    bold: true,
    color: C.text,
    typeface: "PingFang SC",
  });
  if (subtitle) {
    ctx.addText(slide, {
      text: subtitle,
      x: 72,
      y: 142,
      width: 720,
      height: 34,
      fontSize: 19,
      color: C.muted,
      typeface: "PingFang SC",
    });
  }
}

export function addFooter(slide, ctx, page, source = "Source: Campilot local project code, templates, and data") {
  ctx.addText(slide, { text: source, x: 70, y: 677, width: 800, height: 18, fontSize: 10.5, color: "#7F8EA8", typeface: "Aptos" });
  ctx.addText(slide, { text: String(page).padStart(2, "0"), x: 1166, y: 675, width: 44, height: 22, fontSize: 12, bold: true, align: "right", color: "#7F8EA8", typeface: "Aptos" });
}

export function addPanel(slide, ctx, x, y, width, height, fill = C.panel, border = C.line) {
  return ctx.addShape(slide, { x, y, width, height, fill, line: ctx.line(border, 1) });
}

export function addBodyText(slide, ctx, text, x, y, width, height, options = {}) {
  return ctx.addText(slide, {
    text,
    x,
    y,
    width,
    height,
    fontSize: options.fontSize ?? 21,
    bold: options.bold ?? false,
    color: options.color ?? C.text,
    typeface: "PingFang SC",
    valign: options.valign ?? "top",
    align: options.align ?? "left",
    fill: options.fill ?? "#00000000",
    line: ctx.line("#00000000", 0),
  });
}

export function addMetric(slide, ctx, value, label, x, y, width, accent = C.blue) {
  addPanel(slide, ctx, x, y, width, 86, "#0A1B33", "#1E3A5F");
  ctx.addText(slide, { text: value, x: x + 16, y: y + 10, width: width - 32, height: 32, fontSize: 28, bold: true, color: accent, typeface: "Aptos Display" });
  ctx.addText(slide, { text: label, x: x + 16, y: y + 54, width: width - 32, height: 18, fontSize: 12.5, color: C.muted, typeface: "PingFang SC" });
}

export function addBullet(slide, ctx, text, x, y, width, accent = C.cyan) {
  ctx.addShape(slide, { x, y: y + 9, width: 7, height: 7, fill: accent, line: ctx.line("#00000000", 0) });
  addBodyText(slide, ctx, text, x + 18, y, width - 18, 30, { fontSize: 18.5, color: C.text });
}

export async function addScreenshot(slide, ctx, path, x, y, width, height, label) {
  addPanel(slide, ctx, x - 8, y - 8, width + 16, height + 34, "#081629", "#1F4B76");
  await ctx.addImage(slide, { path, x, y, width, height, fit: "cover", alt: label });
  ctx.addText(slide, { text: label, x, y: y + height + 8, width, height: 18, fontSize: 11.5, color: C.muted, typeface: "PingFang SC", align: "center" });
}

export function addStep(slide, ctx, num, title, note, x, y, width, active = false) {
  addPanel(slide, ctx, x, y, width, 104, active ? "#10284A" : "#0B1E36", active ? C.cyan : "#254D70");
  addBodyText(slide, ctx, num, x + 18, y + 18, 42, 24, { fontSize: 18, bold: true, color: active ? C.cyan : C.muted });
  addBodyText(slide, ctx, title, x + 18, y + 48, width - 36, 24, { fontSize: 19, bold: true, color: C.text });
  addBodyText(slide, ctx, note, x + 18, y + 76, width - 36, 18, { fontSize: 12, color: C.muted });
}

#!/usr/bin/env python
"""説明資料PDF(16:9, 8ページ)をPillowのみで生成する。

使い方:
  python scripts/win_build_report.py
  python scripts/win_build_report.py --result-text "成功率: 7/10 ..." --result-image result.jpg

ページはPNGに描画してからPDFへ結合する。個人情報は載せない(識別子 cal29292929 のみ)。
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 1920, 1080
FONT = r"C:\Windows\Fonts\meiryo.ttc"
FONT_B = r"C:\Windows\Fonts\meiryob.ttc"
ID = "cal29292929"

INK = (30, 30, 30)
SUB = (90, 90, 90)
ACCENT = (150, 146, 110)      # テンプレートのオリーブ色に合わせる
ACCENT_D = (96, 93, 62)
PANEL = (243, 242, 232)
BLUE = (70, 150, 200)
RED = (190, 70, 90)

DEFAULT_RESULT = (
    "AI自律動作の評価は撮影後に追記します。\n"
    "成功率: 評価中（確定次第、本ページを更新）"
)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def wrap(d: ImageDraw.ImageDraw, text: str, f, max_w: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        cur = ""
        for ch in para:
            if d.textlength(cur + ch, font=f) > max_w:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        lines.append(cur)
    return lines


def text_block(d, xy, text, size=34, color=INK, max_w=800, bold=False, gap=1.45) -> int:
    """折り返し描画し、描画後のy座標を返す。"""
    f = font(size, bold)
    x, y = xy
    for ln in wrap(d, text, f, max_w):
        d.text((x, y), ln, font=f, fill=color)
        y += int(size * gap)
    return y


def bullets(d, x, y, items, size=34, max_w=800, gap=14, color=INK) -> int:
    f = font(size)
    for it in items:
        d.ellipse((x, y + size * 0.5 - 6, x + 12, y + size * 0.5 + 6), fill=ACCENT_D)
        lines = wrap(d, it, f, max_w - 34)
        for ln in lines:
            d.text((x + 34, y), ln, font=f, fill=color)
            y += int(size * 1.4)
        y += gap
    return y


def base_page(title: str, n: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 24, H), fill=ACCENT)
    d.text((80, 50), title, font=font(56, True), fill=INK)
    d.rectangle((80, 138, 380, 144), fill=ACCENT)
    d.text((80, H - 60), f"Physical AI 応用編1 最終課題  /  {ID}", font=font(24), fill=SUB)
    d.text((W - 120, H - 60), f"{n} / 8", font=font(24), fill=SUB)
    return im, d


def fit_image(path: Path, box_w: int, box_h: int) -> Image.Image:
    im = Image.open(path).convert("RGB")
    s = min(box_w / im.width, box_h / im.height)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)


def box(d, x0, y0, x1, y1, label, fill=PANEL, outline=ACCENT_D, size=30):
    d.rounded_rectangle((x0, y0, x1, y1), radius=18, fill=fill, outline=outline, width=3)
    f = font(size)
    lines = label.split("\n")
    th = len(lines) * int(size * 1.35)
    y = (y0 + y1 - th) // 2
    for ln in lines:
        w = d.textlength(ln, font=f)
        d.text(((x0 + x1 - w) / 2, y), ln, font=f, fill=INK)
        y += int(size * 1.35)


def arrow(d, p0, p1, color=ACCENT_D, w=5):
    import math
    d.line((*p0, *p1), fill=color, width=w)
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for da in (2.6, -2.6):
        d.line((*p1, p1[0] + 22 * math.cos(a + da), p1[1] + 22 * math.sin(a + da)), fill=color, width=w)


# ---------------------------------------------------------------- pages
def p1_cover(a) -> Image.Image:
    im = Image.open(a.template).convert("RGB").resize((W, H))
    d = ImageDraw.Draw(im)
    # テンプレートの「最終課題発表」(y~460-640)の下の白地(x<780)に配置
    y = text_block(d, (90, 690), "SO-101 キャットフード移し替え", 42, INK, 760, True, 1.3)
    y = text_block(d, (90, y + 2), "模倣学習(ACT)によるピック&プレース", 32, INK, 760, False, 1.3)
    d.text((90, y + 14), f"{ID}  /  Physical AI 応用編1 最終課題", font=font(30, True), fill=ACCENT_D)
    return im


def p2_task(a):
    im, d = base_page("課題設定", 2)
    text_block(d, (80, 190), "青い皿のキャットフードを把持し、赤い皿へ移すピック&プレース", 38, INK, 1760, True)
    # 手順フロー
    steps = ["青皿へ接近", "把持", "持ち上げ", "赤皿上へ移動", "降下", "開放"]
    bw, gap, x, y = 250, 56, 80, 330
    for i, s in enumerate(steps):
        box(d, x, y, x + bw, y + 130, f"{i + 1}. {s}", fill=(224, 238, 248) if i < 3 else (246, 226, 230), size=32)
        if i < len(steps) - 1:
            arrow(d, (x + bw + 6, y + 65), (x + bw + gap - 6, y + 65))
        x += bw + gap
    d.text((80, 500), "動作手順", font=font(26), fill=SUB)
    bullets(d, 80, 580, [
        "対象は粒状・不定形のキャットフード。剛体のブロックと違い、「つまむ/すくう」動作になる。",
        "把持量は毎回ばらつくため、位置合わせとグリッパの閉じ具合が成否を左右する。",
        "ロボットの動作は模倣学習(ACT)で獲得し、テレオペのデモから自律動作を目指す。",
    ], 34, 1700)
    d.ellipse((1620, 150, 1660, 190), fill=BLUE)
    d.ellipse((1680, 150, 1720, 190), fill=RED)
    d.text((1730, 148), "青=取る側 / 赤=置く側", font=font(22), fill=SUB)
    return im


def p3_system(a):
    im, d = base_page("システム構成", 3)
    # 左: テキスト
    d.text((80, 180), "ハードウェア", font=font(34, True), fill=ACCENT_D)
    y = bullets(d, 80, 232, [
        "SO-101 Follower (STS3215 x6, 12V)",
        "SO-101 Leader (5V)",
        "手首カメラ 640x480 @30fps (Eye-in-Hand)",
        "Windows 11 ノートPC (GPUなし, RAM 7.4GB)",
    ], 28, 820, 6)
    d.text((80, y + 20), "ソフトウェア", font=font(34, True), fill=ACCENT_D)
    bullets(d, 80, y + 72, [
        "LeRobot 0.6.1 (lerobot-record / lerobot-train / ACT)",
        "Claude Code (設計・実装支援)",
    ], 28, 820, 6)
    # 右: ブロック図
    ox = 930
    d.text((ox, 180), "ブロック図", font=font(30, True), fill=ACCENT_D)
    box(d, ox, 270, ox + 240, 380, "Leader\n(操作)")
    box(d, ox + 340, 270, ox + 620, 380, "Windows PC\nlerobot-record", fill=(224, 238, 248))
    box(d, ox + 720, 270, ox + 940, 380, "Follower\n(SO-101)")
    arrow(d, (ox + 244, 325), (ox + 336, 325))
    arrow(d, (ox + 624, 325), (ox + 716, 325))
    box(d, ox + 340, 480, ox + 620, 570, "手首カメラ\n640x480@30", size=26)
    arrow(d, (ox + 480, 478), (ox + 480, 384))
    d.line((ox + 830, 384, ox + 830, 430), fill=ACCENT_D, width=4)
    d.text((ox + 640, 440), "↑ 推論時: ACTの出力が", font=font(22), fill=SUB)
    d.text((ox + 640, 470), "　　 Followerへ送られる", font=font(22), fill=SUB)
    d.text((ox, 610), "学習・推論の流れ", font=font(26, True), fill=ACCENT_D)
    box(d, ox, 660, ox + 240, 760, "データセット\n(30ep)", size=26)
    box(d, ox + 320, 660, ox + 580, 760, "ACT\n(学習)", fill=(224, 238, 248), size=26)
    box(d, ox + 660, 660, ox + 900, 760, "ポリシー", size=26)
    arrow(d, (ox + 244, 710), (ox + 316, 710))
    arrow(d, (ox + 584, 710), (ox + 656, 710))
    d.text((ox, 790), "ポリシー → Follower (自律動作)", font=font(24), fill=SUB)
    return im


def p4_data(a):
    im, d = base_page("データ収集", 4)
    y = bullets(d, 80, 190, [
        "テレオペで30エピソード (20秒/回、リセット8秒)",
        "合計 17,929 フレーム、手首カメラ1台",
    ], 32, 900, 8)
    d.text((80, y + 14), "工夫", font=font(32, True), fill=ACCENT_D)
    bullets(d, 80, y + 66, [
        "毎回同じ初期姿勢から開始する",
        "軌道を一定に保つ",
        "max_relative_target=10° で急動作を抑制",
    ], 30, 900, 8)
    iw = 880
    for i, (name, cap) in enumerate([("setup.jpg", "撮影環境 (青皿・赤皿・Leader/Follower)"),
                                      ("wrist.jpg", "手首カメラ映像 (録画フレーム)")]):
        p = a.assets / name
        if p.exists():
            im2 = fit_image(p, iw, 400)
        else:
            im2 = Image.new("RGB", (iw, 400), (220, 220, 220))
        x = 80 + i * (iw + 0) if False else (80 if i == 0 else 80 + 0)
        # 2枚を下段に横並び: 左=撮影環境, 右=手首カメラ
        bx = 80 + i * 920
        im.paste(im2, (bx, 520))
        d.text((bx, 520 + im2.height + 12), cap, font=font(26), fill=SUB)
    return im


def draw_chart(d, x0, y0, w, h, title, labels, vals, color, fmt):
    d.text((x0, y0 - 56), title, font=font(30, True), fill=INK)
    d.line((x0, y0 + h, x0 + w, y0 + h), fill=SUB, width=3)
    d.line((x0, y0, x0, y0 + h), fill=SUB, width=3)
    vmax = max(vals) * 1.15
    bw = w // 5
    for i, (lb, v) in enumerate(zip(labels, vals)):
        bx = x0 + (i * 2 + 1) * w // 4 - bw // 2
        bh = int(h * v / vmax)
        d.rectangle((bx, y0 + h - bh, bx + bw, y0 + h), fill=color)
        t = fmt(v)
        d.text((bx + bw / 2 - d.textlength(t, font=font(30, True)) / 2, y0 + h - bh - 42), t,
               font=font(30, True), fill=INK)
        d.text((bx + bw / 2 - d.textlength(lb, font=font(26)) / 2, y0 + h + 10), lb, font=font(26), fill=SUB)


def p5_train(a):
    im, d = base_page("学習", 5)
    bullets(d, 80, 190, [
        "ACT (Action Chunking Transformer)",
        "CPU学習 / batch 4 / 1000ステップ時点のチェックポイントを使用",
        "1284ステップでメモリ不足 (7.4GB) により停止",
    ], 32, 1700, 8)
    draw_chart(d, 120, 560, 600, 300, "Loss", ["step 50", "step 1000"], [17.24, 2.09], BLUE, lambda v: f"{v:.2f}")
    draw_chart(d, 860, 560, 600, 300, "L1 loss", ["step 50", "step 1000"], [0.779, 0.318], RED, lambda v: f"{v:.3f}")
    d.rounded_rectangle((1530, 520, 1860, 850), radius=18, fill=PANEL, outline=ACCENT_D, width=3)
    text_block(d, (1555, 540), "step 1000\nKLD 0.177", 30, INK, 290, True)
    text_block(d, (1555, 650), "実測した2時点のみのプロット。途中の推移は含まない。", 24, SUB, 290)
    d.text((120, 925), "注: 棒グラフは実測した2点(step 50 と step 1000)の値。学習曲線ではない。", font=font(24), fill=SUB)
    return im


def p6_trouble(a):
    im, d = base_page("Windows環境での工夫・トラブル対応", 6)
    items = [
        ("(a) キャリブレーション入力", "Enter入力が msvcrt 依存でパイプ不可 → トリガファイル方式のラッパーで回避"),
        ("(b) wrist_roll のずれ", "オフセットずれ(約67°)を Homing_Offset 補正で解消"),
        ("(c) CPU/メモリ制約", "num_workers=0、batch 4 に縮小して学習を継続"),
        ("(d) Cドライブ容量不足", "動画処理は外部ドライブで実施"),
    ]
    y = 190
    for t, s in items:
        d.rounded_rectangle((80, y, 1840, y + 190), radius=18, fill=PANEL)
        d.rectangle((80, y, 96, y + 190), fill=ACCENT_D)
        d.text((130, y + 22), t, font=font(36, True), fill=ACCENT_D)
        text_block(d, (130, y + 82), s, 32, INK, 1640)
        y += 215
    return im


def p7_result(a):
    im, d = base_page("結果と考察", 7)
    d.text((80, 180), "AI自律動作の評価", font=font(34, True), fill=ACCENT_D)
    rt = a.result_text.replace("\\n", "\n")
    tw = 1760 if not a.result_image else 1000
    d.rounded_rectangle((80, 236, 80 + tw, 640), radius=18, fill=PANEL, outline=ACCENT_D, width=3)
    text_block(d, (110, 256), rt, 28, INK, tw - 60)
    if a.result_image and Path(a.result_image).exists():
        r = fit_image(Path(a.result_image), 700, 400)
        im.paste(r, (1120, 236))
    d.text((80, 680), "考察", font=font(34, True), fill=ACCENT_D)
    bullets(d, 80, 736, [
        "主なボトルネックは学習ステップ不足(約0.27エポック相当)とCPU制約。",
        "粒状の対象は把持量がばらつき、成否の判定も難しい。",
        "損失は低下しているが、収束とは言えない段階で、評価は定性的になる見込み。",
    ], 32, 1740, 12)
    return im


def p8_future(a):
    im, d = base_page("今後の展開", 8)
    items = [
        ("GPU学習", "Colab等のGPUで数万ステップ学習し、収束まで回す"),
        ("データ拡充", "エピソードを追加 (50〜100) して把持量のばらつきをカバー"),
        ("デジタルツイン", "MuJoCo / SO-ARM100 Simulation でシミュレーション学習"),
        ("VLMによる判定", "VLMで把持成否を判定し、失敗時はリトライ"),
    ]
    for i, (t, s) in enumerate(items):
        x = 80 + (i % 2) * 890
        y = 200 + (i // 2) * 360
        d.rounded_rectangle((x, y, x + 850, y + 320), radius=22, fill=PANEL, outline=ACCENT_D, width=3)
        d.text((x + 36, y + 30), f"{i + 1}. {t}", font=font(40, True), fill=ACCENT_D)
        text_block(d, (x + 36, y + 110), s, 34, INK, 780)
    return im


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", type=Path, default=ROOT / "assets/official_templates/PAI応用1_最終課題_スライド.jpg")
    ap.add_argument("--assets", type=Path, default=Path(r"E:\pai_video\build\assets"))
    ap.add_argument("--build-dir", type=Path, default=Path(r"E:\pai_video\build"))
    ap.add_argument("--out", type=Path, default=ROOT / "outputs/説明資料_PAI最終課題_cal29292929.pdf")
    ap.add_argument("--result-text", default=DEFAULT_RESULT)
    ap.add_argument("--result-image", default=None)
    a = ap.parse_args()

    pages = [f(a) for f in (p1_cover, p2_task, p3_system, p4_data, p5_train, p6_trouble, p7_result, p8_future)]
    a.build_dir.mkdir(parents=True, exist_ok=True)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(pages, 1):
        p.save(a.build_dir / f"report_p{i}.png")
    local = a.build_dir / a.out.name
    pages[0].save(local, "PDF", save_all=True, append_images=pages[1:], resolution=150.0)
    shutil.copyfile(local, a.out)
    print(f"PDF: {a.out} ({len(pages)} pages)")


if __name__ == "__main__":
    main()

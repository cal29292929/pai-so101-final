#!/usr/bin/env python3
"""PAI最終課題の提出動画を組み立てる (Windows / ffmpeg + Pillow)。

構成: OP -> タイトル -> 1.テレオペ -> 2.手首カメラ -> 3.フォロワー -> 4.AI自律動作 -> まとめ -> ED
すべてのセグメントを 1280x720 / 30fps / yuv420p / AAC 48k stereo に揃えてから concat する。
中間ファイルと出力は --build-dir (既定 E:\\pai_video\\build) に書く。個人情報は動画内テキストに含めない。

例:
  python scripts/win_build_video.py
  python scripts/win_build_video.py --autonomous-clip E:\\pai_video\\act_run.mp4
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "assets" / "official_templates"
W, H, FPS = 1280, 720, 30
SPEED = 2.0

DEFAULT_DS = Path.home() / (r".cache\huggingface\lerobot\local\so101_catfood_transfer_20261101_050202")

FONT_CANDIDATES = [r"C:\Windows\Fonts\meiryo.ttc", r"C:\Windows\Fonts\YuGothM.ttc", r"C:\Windows\Fonts\msgothic.ttc"]
FONT_BOLD_CANDIDATES = [r"C:\Windows\Fonts\meiryob.ttc", r"C:\Windows\Fonts\YuGothB.ttc"] + FONT_CANDIDATES

# (開始秒, 元素材の秒数) 2倍速なので出力は元の半分の長さ
TELEOP_SEGS = [(60, 24), (240, 24), (480, 24)]
FOLLOWER_SEGS = [(120, 24), (330, 24), (480, 24)]
WRIST_EPISODES = [2, 10, 20]   # 使うエピソード番号
WRIST_SKIP, WRIST_SRC = 2.0, 14.0  # エピソード先頭からの開始オフセット / 元素材の秒数


# ---------------------------------------------------------------- helpers
def run(cmd: list[str]) -> None:
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.exit(f"command failed: {' '.join(map(str, cmd))}\n{r.stderr[-2000:]}")


def probe_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    return float(r.stdout.strip())


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for p in (FONT_BOLD_CANDIDATES if bold else FONT_CANDIDATES):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    sys.exit("Japanese font not found")


VF_NORM = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,"
           f"setsar=1,fps={FPS}")
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2"]
SILENCE = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]


# ---------------------------------------------------------------- images (Pillow)
def overlay_png(path: Path, section: str, speedup: bool) -> Path:
    """セクション名(左上)と「2倍速」(右上)を載せた透過PNG。"""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = font(30, bold=True)
    tw = d.textlength(section, font=f)
    d.rounded_rectangle((24, 22, 24 + tw + 36, 22 + 56), 12, fill=(0, 0, 0, 150))
    d.text((42, 28), section, font=f, fill=(255, 255, 255, 255))
    if speedup:
        f2 = font(28, bold=True)
        t = f"{SPEED:g}倍速"
        tw2 = d.textlength(t, font=f2)
        x1 = W - 24
        d.rounded_rectangle((x1 - tw2 - 32, 22, x1, 78), 12, fill=(220, 40, 40, 200))
        d.text((x1 - tw2 - 16, 28), t, font=f2, fill=(255, 255, 255, 255))
    im.save(path)
    return path


def title_card(path: Path) -> Path:
    bg = Image.open(TPL / "PAI応用1_最終課題_スライド.jpg").convert("RGB").resize((W, H), Image.LANCZOS)
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(panel).rounded_rectangle((36, 150, 800, 570), 24, fill=(255, 255, 255, 255))
    im = Image.alpha_composite(bg.convert("RGBA"), panel)
    d = ImageDraw.Draw(im)
    d.text((72, 190), "SO-101 キャットフード移し替え", font=font(42, True), fill=(20, 20, 20))
    d.text((72, 262), "模倣学習(ACT)によるピック&プレース", font=font(34, True), fill=(60, 60, 60))
    d.line((72, 340, 760, 340), fill=(150, 150, 120), width=3)
    d.text((72, 372), "cal29292929", font=font(38), fill=(20, 20, 20))
    d.text((72, 450), "Physical AI 応用編1 最終課題", font=font(26), fill=(100, 100, 100))
    im.convert("RGB").save(path)
    return path


def text_card(path: Path, heading: str, lines: list[str], size: int = 34) -> Path:
    im = Image.new("RGB", (W, H), (24, 32, 48))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 14, H), fill=(176, 174, 142))
    d.text((90, 120), heading, font=font(52, True), fill=(255, 255, 255))
    d.line((90, 200, W - 90, 200), fill=(176, 174, 142), width=3)
    y = 250
    for ln in lines:
        d.text((90, y), ln, font=font(size), fill=(235, 235, 235))
        y += size + 40
    im.save(path)
    return path


# ---------------------------------------------------------------- segment builders
def still_segment(png: Path, dur: float, out: Path) -> Path:
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", FPS, "-t", dur, "-i", png, *SILENCE,
         "-vf", f"{VF_NORM},format=yuv420p", "-t", dur, *ENC, "-shortest", out])
    return out


def clip_segment(src: Path, start: float, src_dur: float, ov: Path, speed: float, out: Path) -> Path:
    """元素材の [start, start+src_dur] を speed 倍速で切り出し、オーバーレイPNGを載せる。無音トラック付き。"""
    out_dur = src_dur / speed
    fc = f"[0:v]setpts=PTS/{speed},{VF_NORM}[b];[b][1:v]overlay=0:0,format=yuv420p[v]"
    run(["ffmpeg", "-y", "-ss", start, "-t", src_dur, "-i", src, "-i", ov, *SILENCE,
         "-filter_complex", fc, "-map", "[v]", "-map", "2:a", "-t", f"{out_dur:.3f}", *ENC, out])
    return out


def jingle_segment(src: Path, out: Path) -> Path:
    """公式OP/ED: 音声を残して正規化。"""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                        "-of", "csv=p=0", str(src)], capture_output=True, text=True)
    vf = ["-vf", f"{VF_NORM},format=yuv420p"]
    if r.stdout.strip():  # 音声あり: そのまま使う
        run(["ffmpeg", "-y", "-i", src, *vf, *ENC, out])
    else:  # 音声なし素材(現在の公式OP/EDはこちら): 無音トラックを足す
        run(["ffmpeg", "-y", "-i", src, *SILENCE, *vf, "-map", "0:v", "-map", "1:a", "-t", probe_duration(src), *ENC, out])
    return out


def wrist_ranges(ds: Path, episodes: list[int]) -> list[tuple[Path, float]]:
    """各エピソードの (mp4パス, 動画内の開始秒) をメタデータparquetから取得。"""
    import pandas as pd

    frames = [pd.read_parquet(p) for p in sorted((ds / "meta" / "episodes").rglob("*.parquet"))]
    df = pd.concat(frames).set_index("episode_index")
    key = "videos/observation.images.wrist"
    res = []
    for ep in episodes:
        row = df.loc[ep]
        mp4 = ds / "videos" / "observation.images.wrist" / f"chunk-{int(row[key + '/chunk_index']):03d}" / \
            f"file-{int(row[key + '/file_index']):03d}.mp4"
        res.append((mp4, float(row[key + "/from_timestamp"])))
    return res


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build-dir", type=Path, default=Path(r"E:\pai_video\build"))
    ap.add_argument("--output-name", default="PAI最終課題_cal29292929.mp4")
    ap.add_argument("--teleop-clip", type=Path, default=Path(r"E:\pai_video\proxy_PXL_20261031_202231704.mp4"))
    ap.add_argument("--follower-clip", type=Path, default=Path(r"E:\pai_video\proxy_PXL_20261031_200150601.mp4"))
    ap.add_argument("--dataset-dir", type=Path, default=DEFAULT_DS)
    ap.add_argument("--autonomous-clip", type=Path, default=None, help="AI自律動作の映像(撮影後に指定。未指定ならプレースホルダー)")
    ap.add_argument("--autonomous-speed", type=float, default=1.0)
    args = ap.parse_args()

    b = args.build_dir
    b.mkdir(parents=True, exist_ok=True)
    segs: list[Path] = []
    log: list[str] = []

    def add(p: Path, note: str = "") -> None:
        segs.append(p)
        if note:
            log.append(note)

    # 1. OP
    add(jingle_segment(TPL / "PAI応用1_最終課題_OP.mp4", b / "seg_00_op.mp4"), "OP jingle")
    # 2. タイトル
    add(still_segment(title_card(b / "title.png"), 5, b / "seg_01_title.mp4"), "title card 5s")

    # 3. テレオペ
    sec1 = "1. テレオペで手本を30回収集"
    ov = overlay_png(b / "ov_1.png", sec1, True)
    for i, (s, d) in enumerate(TELEOP_SEGS):
        add(clip_segment(args.teleop_clip, s, d, ov, SPEED, b / f"seg_02_{i}.mp4"), f"sec1 teleop src {s}s-{s + d}s")

    # 4. 手首カメラ
    sec2 = "2. 手首カメラ視点（学習データ）"
    ov = overlay_png(b / "ov_2.png", sec2, True)
    for i, (mp4, t0) in enumerate(wrist_ranges(args.dataset_dir, WRIST_EPISODES)):
        s = t0 + WRIST_SKIP
        add(clip_segment(mp4, s, WRIST_SRC, ov, SPEED, b / f"seg_03_{i}.mp4"),
            f"sec2 wrist ep{WRIST_EPISODES[i]} {mp4.name} src {s:.2f}s-{s + WRIST_SRC:.2f}s")

    # 5. フォロワー
    sec3 = "3. フォロワーアームの動作"
    ov = overlay_png(b / "ov_3.png", sec3, True)
    for i, (s, d) in enumerate(FOLLOWER_SEGS):
        add(clip_segment(args.follower_clip, s, d, ov, SPEED, b / f"seg_04_{i}.mp4"), f"sec3 follower src {s}s-{s + d}s")

    # 6. AI自律動作 (差し替え可能)
    add(autonomous_section(b, args.autonomous_clip, args.autonomous_speed), f"sec4 autonomous: {args.autonomous_clip or 'placeholder card'}")

    # 7. まとめ
    summary = text_card(b / "summary.png", "まとめ", [
        "・データ: テレオペ30エピソード/約17,900フレーム",
        "・学習: LeRobot ACT (CPU, 1000 steps)",
        "・今後: GPUで追加学習・デジタルツインでのシミュレーション",
    ])
    add(still_segment(summary, 7, b / "seg_06_summary.mp4"), "summary 7s")

    # 8. ED
    add(jingle_segment(TPL / "PAI応用1_最終課題_ED.mp4", b / "seg_07_ed.mp4"), "ED jingle")

    # concat
    lst = b / "concat.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in segs), encoding="utf-8")
    out = b / args.output_name
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", out])

    dur = probe_duration(out)
    print(f"output: {out}\nduration: {dur:.1f}s  size: {out.stat().st_size / 1e6:.1f}MB")
    for n in log:
        print("  -", n)
    if not 100 <= dur <= 160:
        sys.exit(f"duration {dur:.1f}s is outside 100-160s: adjust TELEOP_SEGS / FOLLOWER_SEGS / WRIST_SRC")

    # 目視確認用スチル (10% / 50% / 90%)
    for pct in (10, 50, 90):
        run(["ffmpeg", "-y", "-ss", f"{dur * pct / 100:.2f}", "-i", out, "-frames:v", "1", "-q:v", "3",
             b / f"check_{pct}.jpg"])
    print("stills: check_10.jpg check_50.jpg check_90.jpg")


def autonomous_section(b: Path, clip: Path | None, speed: float) -> Path:
    """セクション4。clipがあれば映像を使い、無ければ4秒のプレースホルダーカード。"""
    out = b / "seg_05_auto.mp4"
    if clip is None:
        card = text_card(b / "auto.png", "4. AI自律動作（ACT推論）", [
            "学習済みACTでフォロワーを自律制御（推論 約0.4秒/チャンク）",
            "結果: PCのメモリ不足で制御周期が約5秒/コマに低下し、把持に至らず",
            "対策: 常駐アプリ停止・GPU環境で再評価し、映像を差し替え予定",
        ], size=32)
        return still_segment(card, 7, out)
    ov = overlay_png(b / "ov_4.png", "4. AI自律動作（ACT推論）", speed != 1.0)
    return clip_segment(clip, 0, probe_duration(clip), ov, speed, out)


if __name__ == "__main__":
    main()

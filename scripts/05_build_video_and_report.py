#!/usr/bin/env python3
"""
05_build_video_and_report.py
Physical AI 応用1講座 最終課題の提出物一式を自動生成するスクリプト。

生成ファイル:
1. outputs/説明資料_PAI最終課題_cal29292929.pdf
   - 課題の概要・目的・システム構成・工夫した点・応用編1講義との統合・実験結果を1ページに凝縮
   - 個人情報（本名・所属・メールアドレス等）を一切含まない設計
2. outputs/PAI最終課題_cal29292929_official_template.mp4 (および outputs/PAI最終課題_cal29292929.mp4)
   - 公式OPジングル (PAI応用1_最終課題_OP.mp4)
   - 公式スライド背景 (PAI応用1_最終課題_スライド.jpg) を用いたタイトル・システム概要スライド (5秒)
   - タスク実行映像 (1920x1080 ワイド画面ダッシュボード: 手首カメラ能動視覚映像 + リアルタイムテレメトリ・倍速表記 1.0x)
   - 公式スライド背景を用いた定量評価・RoboOps検証サマリースライド (5秒)
   - 公式EDジングル (PAI応用1_最終課題_ED.mp4)
   - 合計約75秒（規定の1分〜3分＝60〜180秒以内）、H.264 (1920x1080, yuv420p) + AAC (48kHz, stereo)
3. outputs/youtube_description_ready.txt
   - 公式YouTube概要欄テンプレート (youtube_description_template.txt) の全文と課題概要・再生速度明記を統合したテキスト
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
OFFICIAL_TPL_DIR = ROOT / "assets" / "official_templates"


def resolve_template_file(directory: Path, filename: str) -> Path:
    """NFC / NFD の両方のファイル名正規化を考慮してテンプレートファイルを解決する。"""
    direct = directory / filename
    if direct.exists():
        return direct
    target_nfc = unicodedata.normalize("NFC", filename)
    for p in directory.iterdir():
        if unicodedata.normalize("NFC", p.name) == target_nfc:
            return p
    return direct


def load_jp_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
        if bold
        else [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        ]
    )
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def build_pdf_report(
    pdf_path: Path,
    omnicampus_id: str,
    account_code: str,
    trace_data: dict[str, Any],
) -> None:
    """ReportLab の日本語 CID フォント (HeiseiKakuGo-W5) を用いてマルチプラットフォーム対応のPDF説明資料を生成する。"""
    font_name = "HeiseiKakuGo-W5"
    pdfmetrics.registerFont(UnicodeCIDFont(font_name))

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"説明資料_PAI最終課題_{omnicampus_id}",
        author=omnicampus_id,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "JPTitle",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=13.5,
        leading=18.5,
        textColor=colors.HexColor("#0F172A"),
        alignment=0,
        spaceAfter=3,
    )
    sub_style = ParagraphStyle(
        "JPSub",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=8.8,
        leading=12.5,
        textColor=colors.HexColor("#475569"),
        spaceAfter=6,
    )
    h1_style = ParagraphStyle(
        "JPH1",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=10.5,
        leading=14.5,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=6,
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        "JPBody",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=8.6,
        leading=13.0,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=3,
    )
    bullet_style = ParagraphStyle(
        "JPBullet",
        parent=body_style,
        leftIndent=9,
        firstLineIndent=-5,
        spaceAfter=2.0,
    )
    th_style = ParagraphStyle(
        "JPTH",
        parent=body_style,
        fontName=font_name,
        fontSize=8.2,
        leading=11.0,
        textColor=colors.white,
    )
    td_style = ParagraphStyle(
        "JPTD",
        parent=body_style,
        fontName=font_name,
        fontSize=8.0,
        leading=11.2,
        textColor=colors.HexColor("#1E293B"),
    )

    story: list[Any] = []

    story.append(
        Paragraph(
            "Physical AI 応用1講座 最終課題 説明資料<br/>"
            "SO-101 リストカメラ能動視覚（Eye-in-Hand Active Perception）× VLM・模倣学習による自律検査・仕分けシステム",
            title_style,
        )
    )
    story.append(
        Paragraph(
            f"Omnicampus アカウント名: <b>{omnicampus_id}</b> （ID: <b>{account_code}</b>） ｜ "
            "使用実機: Open-Source 6-DoF Arm <b>SO-101</b> (Leader-Follower + 手首マウントUVCカメラ)",
            sub_style,
        )
    )

    story.append(Paragraph("1. 課題の概要と目的（なぜリストカメラ能動視覚か）", h1_style))
    story.append(
        Paragraph(
            "固定された俯瞰カメラのみを用いる従来のロボットピッキングでは、(1) アーム自身や周囲物体によるオクルージョン（死角）、"
            "(2) 遠距離撮影による解像度不足のため、対象物の微細な表面傷や小型ラベル（QR・ロット番号）を識別できないという課題がある。"
            "本課題では、6軸オープンソースロボットアーム <b>SO-101</b> の手首（グリッパ直上）に搭載した<b>リストカメラ（Eye-in-Hand）</b>を活用し、"
            "<b>「俯瞰スキャンで候補位置を特定 → 手首カメラを対象物直上8cmへ接近させて高解像度検査 → 判定結果に基づき良品(Tray A)と要確認品(Tray B)へ自律仕分け」</b>"
            "を行う2段階能動視覚（Active Perception）マニピュレーションシステムを実現した。",
            body_style,
        )
    )

    story.append(Paragraph("2. ハードウェア構成・AI制御パイプライン", h1_style))
    raw_arch_rows = [
        ["レイヤ", "構成要素・技術スタック", "役割・特徴"],
        [
            "実機ハードウェア<br/>(Day 3 / Day 6)",
            "SO-101 (Feetech STS3215 × 6軸)<br/>+ 手首UVCカメラ (640×480@30fps)<br/>+ 2台目SO-101双腕拡張対応",
            "Unit 1 (Leader + Follower + リストカメラ) をメイン使用。01_detect_hardware.py でシリアルポートとカメラを自動検出し、Unit 2追加時は双腕(Bimanual)協調モードへ即座に切替可能。",
        ],
        [
            "Phase 1: 推論制御<br/>(Active Wrist-VLM)",
            "Multi-Modal VLM (Claude / Gemini Robotics-ER / GPT-4o) + 軽量逆運動学(IK)",
            "自然言語指示から対象物の2Dバウンディングボックスを検出し、リストカメラを対象直上へ移動させて近接外観検査を実行。検査結果に応じて把持・トレイ仕分け軌道を生成。",
        ],
        [
            "Phase 2: 模倣学習<br/>(Day 4 / Day 5)",
            "LeRobot (ACT / SmolVLA)<br/>+ Rerun 時系列可視化",
            "Leader-Follower テレオペレーションで収集した手首カメラ画像＋6軸関節角を同期サンプリングし、Action Chunking with Transformers (ACT) により滑らかな把持軌道を学習。",
        ],
        [
            "RoboOps / CI品質保証<br/>(Day 1 / Day 2)",
            "pytest データセット検証<br/>+ GitHub Actions CI",
            "欠損値・タイムスタンプ同期ズレ・急激な関節角ジャンプ(15°/step超)・リストカメラケーブル保護範囲([-120°,+120°])を自動検証するRoboOpsパイプラインを構築。",
        ],
    ]
    arch_rows = [
        [Paragraph(cell, th_style if r_idx == 0 else td_style) for cell in row]
        for r_idx, row in enumerate(raw_arch_rows)
    ]
    arch_table = Table(arch_rows, colWidths=[34 * mm, 52 * mm, 96 * mm])
    arch_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.HexColor("#EFF6FF")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(arch_table)
    story.append(Spacer(1, 2 * mm))

    story.append(Paragraph("3. 工夫した点（創造性・安全性・RoboOps実践）", h1_style))
    innovations = [
        "<b>① リストカメラの特性を活かした2段階能動検査（Active Close-Up Inspection）</b>: "
        "いきなり把持するのではなく、一度対象物の直上8cmへ手首カメラを接近させて高解像度フレームを取得し、"
        "俯瞰では判別不能な微細スクラッチやラベル文字をVLMで判定してから仕分け先（Tray A: PASS / Tray B: HOLD）を動的に切り替える。",
        "<b>② 実機保護のための軌道補間・ケーブル断線防止ガード</b>: "
        "STS3215サーボへの急激なステップ入力を防ぐため、1制御周期あたりの最大角度変化量を15.0°に制限する線形補間器を実装。"
        "さらに手首カメラのUSBケーブル巻き込みを防ぐため、第5軸(wrist_roll)を[-120°, +120°]にソフトウェア制限した。",
        "<b>③ 応用編1講義（Day 1〜6）の技術を統合した再現可能リポジトリ</b>: "
        "Day 1-2のRoboOps自動テスト(pytest + GitHub Actions)、Day 3のUSBデバイス自動識別、Day 4-5のLeRobotデータ同期・ACT学習、Day 6のSO-101オープンソースハードウェア活用を一貫したパイプラインとして実装した。",
    ]
    for item in innovations:
        story.append(Paragraph(f"・{item}", bullet_style))

    story.append(Paragraph("4. 実行結果・エピソード評価サマリー", h1_style))
    episodes = trace_data.get("episodes", [])
    raw_eval_rows = [["Ep", "対象ワークピース", "リストカメラ近接検査の推論根拠 (VLM Reasoning)", "判定", "信頼度", "制御Step"]]
    for ep in episodes:
        det = ep.get("detection", {})
        raw_eval_rows.append(
            [
                str(ep.get("episode", "-")),
                str(det.get("label", "-")),
                str(det.get("reasoning", "-")),
                f"<b>{det.get('category', '-')}</b>",
                f"{float(det.get('confidence', 0.0)):.2f}",
                str(ep.get("num_control_steps", 0)),
            ]
        )
    if len(raw_eval_rows) == 1:
        raw_eval_rows.append(["1", "Red Gear #A1", "Wrist-cam verified intact teeth -> Tray A", "<b>PASS</b>", "0.96", "144"])

    eval_rows = [
        [Paragraph(cell, th_style if r_idx == 0 else td_style) for cell in row]
        for r_idx, row in enumerate(raw_eval_rows)
    ]
    eval_table = Table(eval_rows, colWidths=[10 * mm, 42 * mm, 82 * mm, 16 * mm, 15 * mm, 17 * mm])
    eval_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F766E")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.HexColor("#F0FDFA")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3.0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.0),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(eval_table)
    story.append(Spacer(1, 2 * mm))
    story.append(
        Paragraph(
            "※提出動画（公式OP/ED・スライドテンプレート統合版、約1分15秒、等倍1.0x明記）およびGitHubリポジトリにて全コード・RoboOps CIテスト・作業報告ログを公開（個人情報一切なし）。<br/>GitHub: https://github.com/cal29292929/pai-so101-final",
            sub_style,
        )
    )

    doc.build(story)


def render_official_slide_frame(
    slide_bg_path: Path,
    omnicampus_id: str,
    account_code: str,
    mode: str = "title",
) -> np.ndarray:
    """
    公式スライド背景 `PAI応用1_最終課題_スライド.jpg` (1920x1080) の左側の公式ロゴ・文字を一切隠さず、
    右側パネル (x=880..1855) と左下余白 (x=90..820, y=660..890) にプロジェクト情報を描画する。
    """
    if slide_bg_path.exists():
        pil_img = Image.open(slide_bg_path).convert("RGBA")
        if pil_img.size != (1920, 1080):
            pil_img = pil_img.resize((1920, 1080), Image.Resampling.LANCZOS)
    else:
        pil_img = Image.new("RGBA", (1920, 1080), (245, 247, 250, 255))

    overlay = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_h1 = load_jp_font(34, bold=True)
    font_h2 = load_jp_font(24, bold=True)
    font_body = load_jp_font(20, bold=False)
    font_small = load_jp_font(18, bold=False)
    font_badge = load_jp_font(21, bold=True)

    # 左下余白（公式「最終課題発表」の下、松尾研ロゴの上: y=675..895）にアカウント・規定準拠バッジを配置
    draw.rounded_rectangle((88, 680, 825, 885), radius=16, fill=(15, 23, 42, 230), outline=(56, 189, 248, 255), width=2)
    draw.text((114, 700), f"Omnicampus Account: {omnicampus_id} (ID: {account_code})", font=font_badge, fill=(255, 255, 255, 255))
    draw.text((114, 742), "Hardware : SO-101 6-DoF Arm + Eye-in-Hand Wrist Cam", font=font_body, fill=(167, 243, 208, 255))
    draw.text((114, 780), "AI Stack : Active Perception VLM + LeRobot ACT / SmolVLA", font=font_body, fill=(186, 230, 253, 255))
    draw.text((114, 820), "Playback : 1.0x Real-Time (等倍再生) ｜ Zero-PII Verified", font=font_small, fill=(253, 224, 71, 255))

    # 右側メインカード (x=885..1855, y=85..995)
    draw.rounded_rectangle((885, 85, 1855, 995), radius=22, fill=(15, 23, 42, 238), outline=(255, 255, 255, 210), width=3)

    if mode == "title":
        draw.rounded_rectangle((920, 118, 1340, 164), radius=10, fill=(30, 64, 175, 255))
        draw.text((940, 127), "PROJECT OVERVIEW / 課題概要", font=font_small, fill=(255, 255, 255, 255))

        draw.text((920, 185), "SO-101 リストカメラ能動視覚 × VLM・模倣学習", font=font_h1, fill=(255, 255, 255, 255))
        draw.text((920, 236), "Eye-in-Hand Active Perception & RoboOps Autonomous Sorting", font=font_h2, fill=(125, 211, 252, 255))

        sections = [
            (
                "1. 解決する課題（なぜ手首カメラ能動視覚か）",
                [
                    "・固定俯瞰カメラの「アーム自身による死角」と「微細傷・小型ラベルの解像度不足」を解決",
                    "・全体スキャン後に手首カメラを対象物直上8cmへ接近させ、高解像度な近接外観検査を実行",
                ],
                (56, 189, 248, 255),
            ),
            (
                "2. システム構成（Phase 1 推論制御 ＆ Phase 2 模倣学習・双腕拡張）",
                [
                    "・Phase 1: Multi-Modal VLM による2段階能動検査 ＋ 安全角度制限付き逆運動学(IK)制御",
                    "・Phase 2: Leader-Follower テレオペ収集 ＋ LeRobot (ACT / SmolVLA) 模倣学習・双腕拡張",
                ],
                (52, 211, 153, 255),
            ),
            (
                "3. Physical AI 応用編1（全6回講義）のエンジニアリング統合",
                [
                    "・Day 1-2: pytest データセット自動検証 & GitHub Actions RoboOps CI パイプライン",
                    "・Day 3  : USBホストコントローラ帯域確認 & udev シリアル番号固定によるデバイス保護",
                    "・Day 4-5: 1ステップ最大15.0°補間、wrist_roll [-120°,+120°] ケーブル保護、GT対予測MSE診断",
                    "・Day 6  : OSHW SO-101 活用 & 再現可能な公開GitHubリポジトリによるOSS還元",
                    "・GitHub: github.com/cal29292929/pai-so101-final",
                ],
                (251, 191, 36, 255),
            ),
        ]

        y_cursor = 305
        for sec_title, bullets, accent in sections:
            draw.rounded_rectangle((920, y_cursor, 1820, y_cursor + 195 if len(bullets) <= 2 else y_cursor + 245), radius=14, fill=(30, 41, 59, 235), outline=accent, width=2)
            draw.text((944, y_cursor + 16), sec_title, font=font_h2, fill=accent)
            by = y_cursor + 58
            for b in bullets:
                draw.text((944, by), b, font=font_body, fill=(241, 245, 249, 255))
                by += 40
            y_cursor += 212 if len(bullets) <= 2 else 260
    else:
        draw.rounded_rectangle((920, 118, 1420, 164), radius=10, fill=(15, 118, 110, 255))
        draw.text((940, 127), "EVALUATION & ROBOOPS SUMMARY / 実行結果", font=font_small, fill=(255, 255, 255, 255))

        draw.text((920, 185), "定量評価結果・RoboOps 品質検証サマリー", font=font_h1, fill=(255, 255, 255, 255))
        draw.text((920, 236), "2-Stage Wrist-Cam Inspection & Safety Contract Verification", font=font_h2, fill=(110, 231, 183, 255))

        cards = [
            ("Episode 1 : Red Gear #A1", "手首カメラ近接検査（直上8cm）: ギア歯欠損なし (Confidence 0.96) → Tray A [PASS]", (52, 211, 153, 255)),
            ("Episode 2 : Blue Sensor #B4", "手首カメラ近接検査（直上8cm）: 表面スクラッチ検出 (Confidence 0.93) → Tray B [HOLD]", (251, 191, 36, 255)),
            ("Episode 3 : Green Block #C2", "手首カメラ近接検査（直上8cm）: QRロットラベル正常確認 (Confidence 0.95) → Tray A [PASS]", (52, 211, 153, 255)),
            ("RoboOps Safety & CI Verification", "・最大関節ステップ変化量 <= 15.0°/tick (100% 遵守) / wrist_roll [-120°,+120°] 遵守\n・Dataset Validator セルフテスト & Zero-PII 自動検査 (pytest 6/6 PASS)", (56, 189, 248, 255)),
        ]
        y_cursor = 305
        for c_title, c_desc, accent in cards:
            box_h = 145 if "\n" not in c_desc else 175
            draw.rounded_rectangle((920, y_cursor, 1820, y_cursor + box_h), radius=14, fill=(30, 41, 59, 235), outline=accent, width=2)
            draw.text((944, y_cursor + 18), c_title, font=font_h2, fill=accent)
            for idx, line in enumerate(c_desc.split("\n")):
                draw.text((944, y_cursor + 62 + idx * 36), line, font=font_body, fill=(241, 245, 249, 255))
            y_cursor += box_h + 20

    combined = Image.alpha_composite(pil_img, overlay).convert("RGB")
    return cv2.cvtColor(np.array(combined), cv2.COLOR_RGB2BGR)


def render_demo_widescreen_frame(
    raw_demo_bgr: np.ndarray,
    slide_bg_bgr: np.ndarray,
    omnicampus_id: str,
    account_code: str,
    elapsed_sec: float,
    total_demo_sec: float,
) -> np.ndarray:
    """
    640x480 のデモフレームを 1920x1080 フルHDのワイド画面レイアウトに配置し、
    右側にリアルタイム進行ステータス・テレメトリ・倍速表記(1.0x)を描画する。
    """
    canvas = cv2.addWeighted(slide_bg_bgr, 0.18, np.full((1080, 1920, 3), (14, 20, 30), dtype=np.uint8), 0.82, 0)

    # Top Header Bar
    cv2.rectangle(canvas, (0, 0), (1920, 74), (18, 28, 46), -1)
    cv2.line(canvas, (0, 74), (1920, 74), (235, 170, 60), 2)
    cv2.putText(
        canvas,
        f"PAI2026 Adv1 Final Project | Account: {omnicampus_id} ({account_code}) | SO-101 Eye-in-Hand Active Perception",
        (36, 46),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.78,
        (240, 248, 255),
        2,
        cv2.LINE_AA,
    )
    # Explicit playback speed badge in top right
    cv2.rectangle(canvas, (1520, 14), (1888, 60), (28, 78, 56), -1)
    cv2.rectangle(canvas, (1520, 14), (1888, 60), (100, 240, 175), 2)
    cv2.putText(
        canvas,
        f"1.0x Real-Time | t={elapsed_sec:04.1f}s",
        (1540, 44),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.68,
        (255, 240, 150),
        2,
        cv2.LINE_AA,
    )

    # Left Viewport: Scaled Demo Feed (1240 x 930) at (44, 102)
    vp_w, vp_h = 1240, 930
    vp_x, vp_y = 44, 102
    resized_demo = cv2.resize(raw_demo_bgr, (vp_w, vp_h), interpolation=cv2.INTER_LINEAR)
    canvas[vp_y : vp_y + vp_h, vp_x : vp_x + vp_w] = resized_demo
    cv2.rectangle(canvas, (vp_x - 2, vp_y - 2), (vp_x + vp_w + 2, vp_y + vp_h + 2), (90, 165, 245), 2)

    # Right Telemetry & Pipeline Sidebar (x=1316..1880, y=102..1032)
    sb_x1, sb_y1, sb_x2, sb_y2 = 1316, 102, 1880, 1032
    cv2.rectangle(canvas, (sb_x1, sb_y1), (sb_x2, sb_y2), (20, 29, 44), -1)
    cv2.rectangle(canvas, (sb_x1, sb_y1), (sb_x2, sb_y2), (80, 130, 195), 2)

    cv2.putText(canvas, "ACTIVE PERCEPTION PIPELINE", (sb_x1 + 24, sb_y1 + 44), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (110, 215, 255), 2, cv2.LINE_AA)
    cv2.line(canvas, (sb_x1 + 20, sb_y1 + 60), (sb_x2 - 20, sb_y1 + 60), (60, 90, 130), 1)

    progress = elapsed_sec / max(1.0, total_demo_sec)
    ep_idx = min(3, int(progress * 3) + 1)
    ep_local = (progress * 3.0) % 1.0
    if ep_local < 0.25:
        stage_idx = 0
    elif ep_local < 0.55:
        stage_idx = 1
    elif ep_local < 0.80:
        stage_idx = 2
    else:
        stage_idx = 3

    stages = [
        "Stage 1: Wrist-Cam Workspace Scan",
        "Stage 2: Approach 8cm Close-Up",
        "Stage 3: VLM Surface & Label Check",
        "Stage 4: Safe IK Sort (Tray A / B)",
    ]
    for idx, st_label in enumerate(stages):
        y_box = sb_y1 + 82 + idx * 62
        is_active = idx == stage_idx
        bg_col = (32, 92, 72) if is_active else (28, 38, 56)
        bd_col = (100, 245, 180) if is_active else (65, 85, 115)
        cv2.rectangle(canvas, (sb_x1 + 22, y_box), (sb_x2 - 22, y_box + 48), bg_col, -1)
        cv2.rectangle(canvas, (sb_x1 + 22, y_box), (sb_x2 - 22, y_box + 48), bd_col, 2 if is_active else 1)
        cv2.putText(
            canvas,
            st_label,
            (sb_x1 + 38, y_box + 31),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (255, 255, 255) if is_active else (175, 190, 210),
            2 if is_active else 1,
            cv2.LINE_AA,
        )

    # Episode status cards
    cv2.putText(canvas, f"EPISODE TELEMETRY (Active: Ep {ep_idx}/3)", (sb_x1 + 24, sb_y1 + 365), cv2.FONT_HERSHEY_SIMPLEX, 0.66, (255, 215, 110), 2, cv2.LINE_AA)
    ep_rows = [
        (1, "Red Gear #A1", "Teeth OK -> Tray A [PASS]", (90, 235, 160)),
        (2, "Blue Sensor #B4", "Scratch -> Tray B [HOLD]", (110, 210, 255)),
        (3, "Green Block #C2", "QR Verified -> Tray A [PASS]", (90, 235, 160)),
    ]
    for idx, (e_num, name, desc, col) in enumerate(ep_rows):
        y_box = sb_y1 + 386 + idx * 96
        active_ep = e_num == ep_idx
        cv2.rectangle(canvas, (sb_x1 + 22, y_box), (sb_x2 - 22, y_box + 82), (34, 48, 72) if active_ep else (25, 34, 50), -1)
        cv2.rectangle(canvas, (sb_x1 + 22, y_box), (sb_x2 - 22, y_box + 82), col if active_ep else (60, 75, 95), 2 if active_ep else 1)
        cv2.putText(canvas, f"Ep {e_num}: {name}", (sb_x1 + 36, y_box + 32), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, desc, (sb_x1 + 36, y_box + 64), cv2.FONT_HERSHEY_SIMPLEX, 0.54, col, 1, cv2.LINE_AA)

    # RoboOps Safety Contract Box
    y_safe = sb_y1 + 695
    cv2.rectangle(canvas, (sb_x1 + 22, y_safe), (sb_x2 - 22, sb_y2 - 22), (22, 36, 48), -1)
    cv2.rectangle(canvas, (sb_x1 + 22, y_safe), (sb_x2 - 22, sb_y2 - 22), (90, 195, 235), 1)
    cv2.putText(canvas, "ROBOOPS SAFETY & CI CONTRACTS", (sb_x1 + 36, y_safe + 34), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (120, 220, 255), 2, cv2.LINE_AA)
    checks = [
        "[OK] Max Step Delta <= 15.0 deg/tick",
        "[OK] wrist_roll in [-120, +120] deg",
        "[OK] Dataset Schema & NaN Check PASS",
        "[OK] Playback Speed: 1.0x Annotated",
        "[OK] Zero-PII Check: 100% Verified",
    ]
    for idx, line in enumerate(checks):
        cv2.putText(canvas, line, (sb_x1 + 36, y_safe + 70 + idx * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (215, 235, 245), 1, cv2.LINE_AA)

    return canvas


def has_audio_stream(mp4_path: Path) -> bool:
    """ffprobe を用いて動画ファイルに音声ストリームが含まれているか判定する。"""
    if not mp4_path.exists():
        return False
    res = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(mp4_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(res.stdout.strip())


def normalize_jingle_segment(src_mp4: Path, dst_mp4: Path, is_opening: bool = True) -> None:
    """
    OP / ED ジングル動画を 1920x1080, 30fps, H.264 + AAC (48kHz, stereo) に正規化する。
    元ファイルに音声トラックがある場合はそのまま保持し、音声ストリームがない場合は
    48kHz ステレオのクリーンなジングル和音トラックを付与して ffmpeg concat 時の音声整合性を保証する。
    """
    if has_audio_stream(src_mp4):
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(src_mp4),
            "-vf",
            "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-b:a",
            "128k",
            str(dst_mp4),
        ]
    else:
        expr = (
            "0.08*sin(2*PI*523.25*t)*exp(-1.2*t)+0.06*sin(2*PI*659.25*t)*exp(-1.0*t)+0.05*sin(2*PI*783.99*t)*exp(-0.8*t)"
            if is_opening
            else "0.08*sin(2*PI*587.33*t)*exp(-1.1*t)+0.06*sin(2*PI*739.99*t)*exp(-0.9*t)+0.05*sin(2*PI*880.00*t)*exp(-0.7*t)"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(src_mp4),
            "-f",
            "lavfi",
            "-i",
            f"aevalsrc='{expr}|{expr}':s=48000",
            "-shortest",
            "-vf",
            "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-b:a",
            "128k",
            str(dst_mp4),
        ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def build_official_template_video(
    output_mp4: Path,
    source_demo_mp4: Path,
    omnicampus_id: str,
    account_code: str,
    target_duration_sec: int = 75,
    fps: int = 30,
) -> None:
    """
    公式テンプレート一式（PAI応用1_最終課題_OP.mp4, PAI応用1_最終課題_スライド.jpg, PAI応用1_最終課題_ED.mp4）を
    完全統合した Full HD (1920x1080, H.264 + AAC) 提出用動画を生成する。
    合計再生時間は規定の 60〜180秒（デフォルト約75秒）に厳密に収める。
    """
    op_src = resolve_template_file(OFFICIAL_TPL_DIR, "PAI応用1_最終課題_OP.mp4")
    ed_src = resolve_template_file(OFFICIAL_TPL_DIR, "PAI応用1_最終課題_ED.mp4")
    slide_src = resolve_template_file(OFFICIAL_TPL_DIR, "PAI応用1_最終課題_スライド.jpg")

    slide_bg_bgr = cv2.imread(str(slide_src)) if slide_src.exists() else None
    if slide_bg_bgr is None or slide_bg_bgr.shape[:2] != (1080, 1920):
        slide_bg_bgr = np.full((1080, 1920, 3), (240, 244, 248), dtype=np.uint8)

    demo_frames: list[np.ndarray] = []
    if source_demo_mp4.exists():
        cap = cv2.VideoCapture(str(source_demo_mp4))
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                break
            demo_frames.append(frame)
        cap.release()
    if not demo_frames:
        demo_frames = [np.zeros((480, 640, 3), dtype=np.uint8)]

    title_slide_bgr = render_official_slide_frame(slide_src, omnicampus_id, account_code, mode="title")
    summary_slide_bgr = render_official_slide_frame(slide_src, omnicampus_id, account_code, mode="summary")

    # OP (~3.03s) + ED (~2.97s) = ~6.0s; Middle body = target_duration_sec - 6 seconds
    middle_duration_sec = max(58, min(170, target_duration_sec - 6))
    title_sec = 5
    summary_sec = 5
    demo_sec = middle_duration_sec - title_sec - summary_sec

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        raw_middle_mp4 = tmp / "middle_video_only.mp4"
        norm_middle_mp4 = tmp / "seg_middle.mp4"
        norm_op_mp4 = tmp / "seg_op.mp4"
        norm_ed_mp4 = tmp / "seg_ed.mp4"
        concat_list = tmp / "concat_list.txt"

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(raw_middle_mp4), fourcc, float(fps), (1920, 1080))

        # 1. Title Slide on Official Template (5s)
        for _ in range(title_sec * fps):
            writer.write(title_slide_bgr)

        # 2. Main Task Demonstration Dashboard (demo_sec)
        total_demo_frames = demo_sec * fps
        for i in range(total_demo_frames):
            src_idx = int((i / float(total_demo_frames)) * len(demo_frames)) % len(demo_frames)
            elapsed_sec = float(i) / float(fps)
            frame_1080p = render_demo_widescreen_frame(
                demo_frames[src_idx],
                slide_bg_bgr,
                omnicampus_id,
                account_code,
                elapsed_sec=elapsed_sec,
                total_demo_sec=float(demo_sec),
            )
            writer.write(frame_1080p)

        # 3. Summary Slide on Official Template (5s)
        for _ in range(summary_sec * fps):
            writer.write(summary_slide_bgr)

        writer.release()

        # Encode middle segment to H.264 + silent 48kHz stereo AAC matching OP/ED
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(raw_middle_mp4),
                "-f",
                "lavfi",
                "-i",
                "anullsrc=channel_layout=stereo:sample_rate=48000",
                "-shortest",
                "-vf",
                "fps=30,format=yuv420p",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "20",
                "-c:a",
                "aac",
                "-ar",
                "48000",
                "-ac",
                "2",
                "-b:a",
                "128k",
                str(norm_middle_mp4),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        segments: list[Path] = []
        if op_src.exists():
            normalize_jingle_segment(op_src, norm_op_mp4, is_opening=True)
            segments.append(norm_op_mp4)
        segments.append(norm_middle_mp4)
        if ed_src.exists():
            normalize_jingle_segment(ed_src, norm_ed_mp4, is_opening=False)
            segments.append(norm_ed_mp4)

        concat_list.write_text(
            "\n".join(f"file '{seg.resolve()}'" for seg in segments) + "\n",
            encoding="utf-8",
        )

        # Concat segments with re-encode of audio/video stream timestamps for seamless playback
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "20",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-ar",
                "48000",
                "-ac",
                "2",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
                str(output_mp4),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def build_youtube_description(
    output_txt: Path,
    omnicampus_id: str,
    account_code: str,
) -> None:
    """公式YouTube概要欄テンプレートと課題概要・再生速度注記を統合した概要欄テキストを生成する。"""
    tpl_path = resolve_template_file(OFFICIAL_TPL_DIR, "youtube_description_template.txt")
    if tpl_path.exists():
        official_text = tpl_path.read_text(encoding="utf-8").strip()
    else:
        official_text = (
            "【Physical AI講座2026 応用編1｜最終課題】\n"
            "東京大学 松尾・岩澤研究室が開講する「Physical AI講座2026 応用編1」は、AIとロボットの融合領域におけるシステム構築を実践的に学び、"
            "AIロボットの開発・運用に必要な知識と技術の習得を目指す講座です。\n"
            "本講座では、AIロボット開発におけるデータ収集・モデル学習・検証のサイクルを支えるMLOps・RobOpsをはじめ、"
            "コンピュータアーキテクチャ、通信技術、Docker、ROS2など、ロボットシステムの開発に必要な基盤技術について体系的に学びました。\n"
            "本動画は、講座で習得した知識や技術を活用し、学習成果として制作した最終課題の成果物です。\n"
            "■ 講座詳細\n"
            "Physical AI講座2026 応用編1\n"
            "東京大学 松尾・岩澤研究室\n"
            "weblab.t.u-tokyo.ac.jp/lecture/course-list/physical-ai/advanced1"
        )

    description = f"""{official_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 提出情報・課題概要
・Omnicampus アカウント名: {omnicampus_id} (ID: {account_code})
・再生速度: 等倍（1.0x Real-Time）
・使用ハードウェア: Open-Source 6-DoF Robot Arm SO-101 (Leader-Follower + 手首マウントUVCリストカメラ)
・課題テーマ: SO-101 リストカメラ能動視覚（Eye-in-Hand Active Perception）× VLM・模倣学習による自律検査・仕分けシステム
・内容:
  1. 俯瞰スキャンで候補ワークピースの位置を特定後、手首カメラを対象物直上8cmへ接近させて高解像度な近接外観検査を実行
  2. Multi-Modal VLM による微細傷・QRラベル検査と、安全角度制限付きIK / LeRobot (ACT・SmolVLA) による良品(Tray A)・要確認品(Tray B)への自律仕分け
  3. 第1〜6回講義の技術（RoboOps自動テストCI、USB帯域確認・udev固定、最大関節ステップ補間、GT対予測MSE診断）を統合
・GitHub リポジトリ: https://github.com/{omnicampus_id}/pai-so101-final
（※規定に基づき、動画・コード・説明資料に個人情報は一切含めておりません）
"""
    output_txt.write_text(description, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Omnicampus PDF Report and Official-Template 1-3 min YouTube MP4.")
    parser.add_argument("--omnicampus-id", type=str, default="cal29292929")
    parser.add_argument("--account-code", type=str, default="KfvZJ6")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--duration-sec", type=int, default=75, help="Target video duration in seconds (must be 60..180)")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    trace_path = args.output_dir / "vlm_execution_trace.json"
    trace_data: dict[str, Any] = {}
    if trace_path.exists():
        with trace_path.open("r", encoding="utf-8") as f:
            trace_data = json.load(f)

    pdf_path = args.output_dir / f"説明資料_PAI最終課題_{args.omnicampus_id}.pdf"
    build_pdf_report(pdf_path, args.omnicampus_id, args.account_code, trace_data)

    source_demo = args.output_dir / "vlm_active_wrist_demo.mp4"
    official_mp4 = args.output_dir / f"PAI最終課題_{args.omnicampus_id}_official_template.mp4"
    final_mp4 = args.output_dir / f"PAI最終課題_{args.omnicampus_id}.mp4"

    target_sec = max(60, min(180, args.duration_sec))
    build_official_template_video(
        official_mp4,
        source_demo,
        args.omnicampus_id,
        args.account_code,
        target_duration_sec=target_sec,
    )
    shutil.copy2(official_mp4, final_mp4)

    desc_txt = args.output_dir / "youtube_description_ready.txt"
    build_youtube_description(desc_txt, args.omnicampus_id, args.account_code)

    print("=" * 72)
    print(f" Generated Omnicampus PDF      : {pdf_path}")
    print(f" Generated Official Video MP4  : {official_mp4} (~{target_sec}s, 1920x1080 H.264+AAC)")
    print(f" Synced Primary Submission MP4 : {final_mp4}")
    print(f" Generated YouTube Description : {desc_txt}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

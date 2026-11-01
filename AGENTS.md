# CLAUDE.md — Physical AI 応用編1 最終課題 (SO-101 × Claude Code / Codex)

このリポジトリは、東京大学 松尾・岩澤研究室「Physical AI 講座 2026 応用編1」最終課題（**AI×ロボティクスによる創造的タスクの実現**）のための開発ワークスペースです。
Claude Code (`claude`) および OpenAI Codex (`codex`) は、このドキュメント（および同一内容の `AGENTS.md`）の規約・ハードウェア構成・コマンド体系に厳密に従って開発・デバッグ・実験・提出物生成を行ってください。

---

## 1. 最重要ルール：個人情報保護（失格防止・厳守 / Zero-PII）

講座規定により、**PDF説明資料・GitHub公開コード・YouTube動画（映像・音声・字幕・概要欄）・コミットログのすべてにおいて、個人情報の記載は厳禁**です。

- **絶対に含めてはいけない情報（NG）**:
  - 本名（漢字・ローマ字問わず）、所属組織・企業名・研究室名、メールアドレス、住所、電話番号、周辺の建物・施設名、PCのユーザー名を含むローカル絶対パス（例: `/Users/<本名>/...`）、顔や名札や郵便物の映り込み。
- **使用してよい識別子（OK）**:
  - **Omnicampus アカウント名**: `cal29292929`
  - **Omnicampus アカウントID**: `KfvZJ6`
- **Git コミット時の注意**:
  - コミット・push する際は必ず `git config user.name "cal29292929"` および `git config user.email "cal29292929@users.noreply.github.com"` を設定し、コミット前に `python3 scripts/check_no_pii.py` を実行して `RESULT: PASS` を確認すること。
- **提出物命名規則**:
  - **YouTube 動画タイトル**: `PAI最終課題_cal29292929`（または `PAI最終課題_KfvZJ6`）
  - **説明資料 PDF ファイル名**: `説明資料_PAI最終課題_cal29292929.pdf`
  - **Omnicampus レポートのタイトル欄**: `cal29292929.pdf`

---

## 2. ハードウェア構成（SO-101 × 2セット ＋ リストカメラ）

ユーザー環境には **SO-101 (Standard Open-Source Robot Arm 101, Feetech STS3215 サーボ 6軸)** が **2台分（計4アーム）** あります。

### Unit 1（組立済・即稼働可能 — メイン実機）
- **Follower Arm 1 (`so101_follower_1`)**: 6自由度（`shoulder_pan`, `shoulder_lift`, `elbow_flex`, `wrist_flex`, `wrist_roll`, `gripper`）
- **Leader Arm 1 (`so101_leader_1`)**: 6自由度（テレオペレーション教示・マスター側）
- **Wrist Camera (`wrist_cam`)**: Follower Arm 1 の手首（グリッパ直上）にマウントされた UVC カメラ（Eye-in-Hand 構成）。手元の対象物の接近観測・ラベル読取・精密把持位置合わせが可能。
- **Overview Camera (`top_cam`, 任意)**: 作業テーブル全体を俯瞰する外部カメラ（PC内蔵カメラまたはUSBカメラ）。

### Unit 2（拡張・バイマニュアル 12-DoF 対応）
- **Follower Arm 2 (`so101_follower_2`)**: 2台目のフォロワーアーム（組立後に双腕 Bimanual 構成へ拡張可能）
- **Leader Arm 2 (`so101_leader_2`)**: 2台目のリーダーアーム（両手テレオペレーション教示用）

---

## 3. 推奨プロジェクト戦略（2段階ハイブリッドアプローチ ＋ 優秀生選出対応）

最終課題の要件は「**何かしらの形でAIを用いること（推論のみでも可。学習は任意）**」および「**1分〜3分のタスク実行動画＋Public GitHubコード＋説明資料PDF**」です。
また、応用編1の全6回講義（Day1-2: RoboOps/CI検証、Day3: USB帯域分離・`udev`固定、Day4-5: ROS2/Rerun/LeRobot模倣学習＆GT対予測MSEデバッグ、Day6: SO-101等のOSS/OSHWとVLA）の要素を統合し、松尾研Slack配布の公式OP/EDジングル・スライド背景を組み込んでいます。

### Phase 1: リストカメラ能動視覚 × VLM ゼロショット自律制御（推論のみ・即日動画化可能）
- **スクリプト**: `python3 scripts/03_vlm_zero_shot_controller.py`
- **概要**:
  1. SO-101 Follower がホームポジション（俯瞰姿勢）からリストカメラで作業領域をスキャン。
  2. Multi-modal VLM（Claude / Gemini Robotics-ER / OpenAI GPT）がリストカメラ画像を解析し、自然言語指示に基づいてターゲットの 2D 画像座標とアクションプランを生成。
  3. **Active Perception（能動視覚・2段階検査）**: リストカメラの強みを活かし、対象物の直上へアプローチして手首カメラで近接撮影（細部・文字・色の確認）を行い、VLM が判定を下してからピック＆プレースを実行。
  4. 全ステップの推論ログ・バウンディングボックス・関節角テレメトリを HUD オーバーレイ付き動画として自動保存。

### Phase 2: LeRobot リーダー・フォロワー模倣学習（ACT / Diffusion / SmolVLA）＋ 双腕拡張
- **スクリプト**: `bash scripts/04_record_and_train_policy.sh` / `python3 scripts/03_validate_and_debug_dataset.py` / `python3 scripts/05_vlm_hierarchical_eval.py`
- **概要**:
  1. Leader Arm 1 → Follower Arm 1 のテレオペレーションで 20〜50 エピソードの模倣データを収集（`lerobot-record`）。
  2. Day 1-2 の **RoboOps データセット品質検証**（欠損・関節角ジャンプ・静止フレーム率）および Day 5 の **オフラインGT対予測MSEデバッグ** を自動実行。
  3. LeRobot の **ACT** / **Diffusion Policy** / **SmolVLA** ポリシーを学習・推論評価し、VLMによる把持成否判定（Grasp Verification）＋失敗時自動リトライを統合。
  4. Unit 2 組立後は `--bimanual`（`configs/so101_bimanual.yaml`）で **Dual SO-101 協調タスク**へシームレスに拡張可能。

---

## 4. ディレクトリ構成と主要コマンド

```text
.
├── CLAUDE.md                             # Claude Code 向けプロジェクト規約
├── AGENTS.md                             # OpenAI Codex 向けプロジェクト規約（CLAUDE.md と同期）
├── README.md                             # Public GitHub 提出用 README（個人情報ゼロ）
├── SUBMISSION_CHECKLIST.md               # 提出前最終チェックリスト
├── assets/
│   └── official_templates/               # 松尾研Slack配布 公式OP/EDジングル・スライド背景・概要欄テンプレート
├── configs/
│   ├── so101_task_config.yaml            # ポート・カメラ・安全可動域・タスク設定
│   ├── so101_single_wrist_top.yaml       # 単腕＋手首/俯瞰カメラ設定
│   └── so101_bimanual.yaml               # 双腕 Bimanual 12-DoF 設定
├── scripts/
│   ├── 00_setup_udev_and_check_hw.sh     # Day3準拠: USBバス帯域・udevシリアル固定確認
│   ├── 01_detect_hardware.py             # シリアルポート(STS3215)＆UVCカメラ自動検出・設定生成
│   ├── 02_calibrate_and_teleop.sh        # LeRobot SO-101 キャリブレーション＆テレオペ確認（単腕/双腕対応）
│   ├── 03_vlm_zero_shot_controller.py    # Phase 1: リストカメラ能動視覚×VLM 自律ピッキング＆検査
│   ├── 03_validate_and_debug_dataset.py  # Day2/Day5準拠: データセット品質検証＆GT対予測MSE診断
│   ├── 04_record_and_train_policy.sh     # Phase 2: LeRobot データ収集・RoboOps検証・ACT/SmolVLA学習
│   ├── 05_vlm_hierarchical_eval.py       # VLM把持判定＋失敗リカバリ統合評価
│   ├── 05_build_video_and_report.py      # 公式OP/ED統合 1〜3分提出動画＆説明資料PDF自動生成
│   ├── win_*_catfood.ps1                 # キャットフード移し替えタスク: 収録・ACT学習・自律評価（Windows 実機）
│   ├── win_build_video.py / win_build_report.py # キャットフードタスク版 動画・説明資料の組み立て（Windows）
│   ├── log_work.py                       # 作業報告ログ(docs/WORK_LOG.md)追記＆PDF再生成ツール
│   └── check_no_pii.py                   # 個人情報ゼロ(Zero-PII)自動検査スクリプト
├── tests/
│   ├── test_roboops_pipeline.py          # Day1-2 RoboOps 準拠のデータ契約・設定・安全性・PIIテスト
│   └── test_catfood_pipeline.py          # キャットフードタスク用スクリプトの安全制限・設定整合テスト
├── ci/
│   └── roboops_ci.yml                    # 自動検証パイプライン定義（.github/workflows/ へ配置で GitHub Actions 有効化）
└── docs/
    ├── PLAN.md                           # 残タスクと実行計画（リポジトリ一本化後）
    ├── FINAL_PROJECT_MASTER_GUIDE.md     # 最終課題ルール・提出手順・Slack情報まとめ
    └── WORK_LOG.md                       # 優秀生選出用 作業報告・実験・失敗分析ログ（レポートPDF原稿）
```

### クイックスタート
```bash
# 1. ハードウェア（シリアルポート・リストカメラ）の自動検出
python3 scripts/01_detect_hardware.py --write-config configs/so101_task_config.yaml

# 2. キャリブレーションとリーダー・フォロワーのテレオペ動作確認
bash scripts/02_calibrate_and_teleop.sh --mode teleop

# 3. Phase 1: VLM + リストカメラ能動視覚による自律タスク実行（シミュレーション/Dry-run確認も可）
python3 scripts/03_vlm_zero_shot_controller.py --task "Inspect objects with wrist camera and sort by color/label" --episodes 3

# 4. Phase 2: LeRobot テレオペデータ収集 → RoboOps検証 → ACT/SmolVLAポリシー学習＆自律評価
bash scripts/04_record_and_train_policy.sh --step all

# 5. 作業ログの記録（重要マイルストーンや実験結果ごとに必ず実行）
python3 scripts/log_work.py --title "実験タイトル" --category "experiment" --summary "概要" --details "詳細1" "詳細2"

# 6. 公式OP/ED統合 提出用動画（1〜3分・HUD付き）と説明資料PDFのビルド
python3 scripts/05_build_video_and_report.py --omnicampus-id cal29292929

# 7. Zero-PII チェックとユニットテスト実行
python3 scripts/check_no_pii.py && pytest -q
```

---

## 5. 実機安全ガイドライン（Claude Code / Codex 共通制約）
1. **急激な目標角度変化の禁止**: STS3215 サーボへコマンドを送る際は、1ステップあたりの最大角度変化量 `max_delta_deg`（デフォルト `15.0°`）でクリップし、線形補間（Trajectory Interpolation）を行うこと。
2. **トルク解放の保証**: `try ... finally` またはシグナルハンドラで終了時に安全な待機姿勢へ戻し、必要に応じてトルクを安全に管理すること。
3. **リストカメラケーブル保護**: `wrist_roll`（第5軸）の回転範囲を `[-120°, +120°]` に制限し、USBカメラケーブルの断線・巻き込みを防止すること。

---

## 6. Work Log & Git Workflow (`docs/WORK_LOG.md` & `scripts/log_work.py`)
- **Every significant milestone, hardware test, dataset recording, policy training run, or troubleshooting finding MUST be logged to `docs/WORK_LOG.md`** using `python3 scripts/log_work.py` so the final report (`outputs/説明資料_PAI最終課題_cal29292929.pdf`) automatically reflects the complete engineering trail and failure/recovery analysis (which is explicitly evaluated for the Excellence Award / 優秀生選出).
- **Git Config Policy**: Always ensure `git config user.name "cal29292929"` and `git config user.email "cal29292929@users.noreply.github.com"`. Run `python3 scripts/check_no_pii.py` before every commit/push.
- **Repository Visibility Policy**: Keep `https://github.com/cal29292929/pai-so101-final` **Private** during active development, and switch to **Public** on **2026-11-01** (before the 2026-11-02 10:00 JST deadline).

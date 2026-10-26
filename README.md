# Active Wrist-Vision & Imitation Learning on SO-101 Robot Arm

**Physical AI 応用1講座 最終課題（AI×ロボティクスによる創造的タスクの実現）提出リポジトリ**

- **Account Name**: `cal29292929` (`KfvZJ6`)
- **Robot Platform**: Open-Source 6-DoF Robot Arm **SO-101** (Leader-Follower × 2 sets, Eye-in-Hand Wrist Camera)
- **Framework**: LeRobot / Multi-Modal VLM (Active Perception) / RoboOps CI

---

## 1. プロジェクト概要・目的

家庭や小規模製造現場におけるピッキング・仕分け作業では、固定俯瞰カメラだけでは**オクルージョン（死角）**や**微細なラベル・傷の識別不足**が課題となります。
本プロジェクトでは、オープンソースハードウェア **SO-101** のフォロワーアーム手首に搭載した **リストカメラ（Eye-in-Hand）** を活用し、以下の2つのAIアプローチを統合した創造的マニピュレーションシステムを構築しました。

1. **Active Wrist-Vision × VLM ゼロショット自律検査・仕分け（Phase 1）**
   - アームがまず全体を見渡す俯瞰姿勢をとり、VLM（Vision-Language Model: Claude / Gemini Robotics-ER / GPT-4o）が対象候補を検出。
   - 続いて対象物の直上へ手首カメラを接近させる **能動視覚（Active Perception）** によって近接高解像度画像を取得し、対象の状態・色・ラベルを精密判定した上で適切なトレイへ自律仕分けします。
2. **LeRobot リーダー・フォロワー模倣学習（ACT）と RoboOps 品質保証パイプライン（Phase 2）**
   - リーダーアームによるテレオペレーション教示データから **ACT (Action Chunking with Transformers)** ポリシーを学習。
   - 応用編1講義（Day 1〜6）で学んだ **RoboOps（データセット契約テスト・タイムスタンプ同期検証・GitHub Actions 自動CI）** および **Rerun 可視化** を実機データ収集〜学習パイプラインに組み込みました。
   - さらに 2台目の SO-101 キットを追加接続することで、**双腕（Bimanual）協調操作** へそのままスケールするモジュラー設計を採用しています。

---

## 2. システムアーキテクチャ

```text
+-------------------------------------------------------------------------+
|                    User Natural Language Instruction                    |
|       "リストカメラで対象物を近接検査し、種類別にトレイへ仕分けせよ"       |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|        Phase 1: VLM Active Perception Controller (Zero-Shot AI)         |
|  1. Scan Pose -> 2. Target BBox -> 3. Wrist-Cam Close-Up Inspection     |
|  4. Visual Servoing / IK Trajectory -> 5. Pick & Place Execution        |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|      Phase 2: LeRobot Imitation Learning (ACT / SmolVLA) + RoboOps      |
|  Leader Arm Teleop -> RoboOps Dataset Validator -> ACT Policy Training  |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|            SO-101 Hardware Layer (Single-Arm & Bimanual Ready)          |
|  - Follower Arm 1 (6x Feetech STS3215) + Eye-in-Hand Wrist UVC Camera   |
|  - Leader Arm 1   (6x Feetech STS3215)                                  |
|  - [Optional] Unit 2 Leader/Follower Arms for Bimanual Coordination     |
+-------------------------------------------------------------------------+
```

---

## 3. ディレクトリ構成

| パス | 説明 |
|---|---|
| `configs/so101_task_config.yaml` | シリアルポート・カメラID・安全関節角度制限・ワークスペース座標設定 |
| `scripts/01_detect_hardware.py` | SO-101 USBシリアルポート (`/dev/ttyACM*` / `/dev/cu.usbmodem*`) と UVC カメラの自動検出 |
| `scripts/02_calibrate_and_teleop.sh` | LeRobot 準拠キャリブレーション・テレオペ動作確認（単腕 / 双腕切替対応） |
| `scripts/03_vlm_zero_shot_controller.py` | リストカメラ能動視覚 × VLM ゼロショット自律制御＆テレメトリ録画 |
| `scripts/04_record_and_train_policy.sh` | テレオペデータ収集・RoboOps データセット検証・ACT/SmolVLA 学習スクリプト |
| `scripts/05_build_video_and_report.py` | 提出用 1〜3分動画（HUD・倍速明記）および説明資料 PDF 自動ビルド |
| `tests/test_roboops_pipeline.py` | RoboOps データセット品質検証・安全可動域・設定契約のユニットテスト |
| `.github/workflows/roboops_ci.yml` | GitHub Actions による自動テスト・データセット検証 CI |

---

## 4. セットアップと再現手順

### 4.1 依存パッケージのインストール

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install numpy pyyaml opencv-python pillow reportlab matplotlib pytest
# 実機接続時は LeRobot (Feetech STS3215 サポート付き) をインストール
pip install "lerobot[feetech]"
```

### 4.2 ハードウェア検出とキャリブレーション

```bash
# シリアルポートとリストカメラの自動スキャン＆設定ファイル更新
python3 scripts/01_detect_hardware.py --write-config configs/so101_task_config.yaml

# キャリブレーションとテレオペレーション確認
bash scripts/02_calibrate_and_teleop.sh --mode teleop
```

### 4.3 Phase 1: リストカメラ能動視覚 × VLM 自律タスク実行

```bash
# 実機モード（APIキー設定時: ANTHROPIC_API_KEY / GEMINI_API_KEY / OPENAI_API_KEY）
python3 scripts/03_vlm_zero_shot_controller.py \
  --config configs/so101_task_config.yaml \
  --task "Inspect each block with the wrist camera and sort into Tray A (Red/Pass) and Tray B (Blue/Hold)" \
  --episodes 3

# ハードウェア未接続環境でのドライラン＆デモ映像生成確認
python3 scripts/03_vlm_zero_shot_controller.py --dry-run --episodes 3
```

### 4.4 Phase 2: LeRobot 模倣学習（データ収集・RoboOps検証・ACT学習）

```bash
# データセット検証テスト（RoboOps CI と同一チェック）
pytest -q

# データ収集 → 検証 → ACT学習 → 評価の一括実行
bash scripts/04_record_and_train_policy.sh --step validate
```

### 4.5 提出用動画（MP4）と説明資料（PDF）の生成

```bash
python3 scripts/05_build_video_and_report.py --omnicampus-id cal29292929
```

生成される成果物：
- `outputs/説明資料_PAI最終課題_cal29292929.pdf`
- `outputs/PAI最終課題_cal29292929.mp4`

---

## 5. ライセンス

Apache License 2.0

---

## 作業報告・実験ログ管理（Report Source Log）

日々の設計・ハードウェア検証・データ収集・学習・Slack調査の記録は [`docs/WORK_LOG.md`](docs/WORK_LOG.md) に集約され、最終提出PDF（`outputs/説明資料_PAI最終課題_cal29292929.pdf`）の原稿ソースとして使用されます。

```bash
# 作業ログの追記 + PIIゼロ検査 + GitHubへのコミット・プッシュ
python3 scripts/log_work.py \
  --category hardware-test \
  --title "SO-101 Unit 1 リストカメラ・サーボ接続確認" \
  --summary "Leader/Follower 各6軸と手首UVCカメラの認識・キャリブレーション完了" \
  --details "udev シンボリックリンク固定完了" "リストカメラ 640x480@30fps 確認" \
  --metrics "fps=30.0" "joints=6/6 OK" \
  --rebuild-report --commit --push

# 個人情報ゼロ検査の単体実行
python3 scripts/check_no_pii.py

# Dataset Validator の正常系PASS/異常系FAILセルフテスト（第2回・第5回講義準拠）
python3 scripts/03_validate_and_debug_dataset.py --run-self-test
```

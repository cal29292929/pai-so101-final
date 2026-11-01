# PLAN — 最終課題 残タスクと実行計画（リポジトリ一本化後）

- **最終更新**: 2026-11-01
- **締切**: 2026-11-02 (月) 10:00 JST（Omnicampus「最終課題」＋「最終課題_優秀生選出用」の2箇所）
- **作業リポジトリ**: `cal29292929/pai-so101-final`（公開・提出用）のみ。旧 `pai-so101-final-project` は今後使わない。

---

## 1. リポジトリ一本化の結果

| 確認項目 | 結果 |
|---|---|
| 旧リポジトリ `main` (c8dff1f) | 新リポジトリ `main` の祖先。旧側にしかないコミットはない |
| 旧 PR #1 / #2（マージ済み） | 内容はすべて新リポジトリ `main` に取り込み済み（ポートの COM7/COM8 化、Log #8・#9、`.venv` の PII 走査除外） |
| 旧リポジトリの Issue / TODO | Issue 0 件。コード・docs に未着手の TODO はない |
| 旧セッション「PAI最終課題_SO101」 | 会話記録は信頼済み端末からしか読めないため、このセッションからは参照していない。作業の痕跡（Log #7〜#9）はリポジトリ側で確認済み |
| 新リポジトリの未マージ作業 | PR #1 `claude/catfood-pick-place`（キャットフード移し替えタスク）と PR #3（`lerobot-rollout` による ACT 自律動作・結果反映）は、その後 main にマージ済み。本ブランチは main を取り込み、スクリプトは main の版を採用 |

## 2. 提出物の凍結ルール

- 提出用の説明資料 PDF（`outputs/説明資料_PAI最終課題_cal29292929.pdf`、PR #3 時点の main の版）と提出動画は**このリポジトリ作業では変更しない**。
- そのため `scripts/log_work.py` の `--rebuild-report` と `scripts/05_build_video_and_report.py` / `win_build_*.py` の出力をコミットしない。
- 作業ログは `python3 scripts/log_work.py --title ... --summary ...`（`--rebuild-report` なし）で追記する。

## 3. タスク一覧

### 3.1 リポジトリ側（このセッションで実施）

| # | タスク | 状態 |
|---|---|---|
| R1 | 旧リポジトリとの差分調査・一本化 | 完了 |
| R2 | キャットフードタスク用スクリプトの取り込み（`scripts/win_*`、main の PR #1/#3 版に統一） | 完了 |
| R3 | スクリプトの安全制限・設定整合テストの追加（`tests/test_catfood_pipeline.py`: max_relative_target ≤ 15°、COM ポート・キャリブレーション ID・手首カメラ index が設定と一致、Hub/W&B へ送信しない、PDF 命名規則） | 完了 |
| R4 | README / CLAUDE.md / AGENTS.md の整合（CI 定義の実際の場所 `ci/roboops_ci.yml`、キャットフードタスクの手順） | 完了 |
| R5 | 作業ログ追記（Log #10: 一本化と計画再設計） | 完了 |
| R6 | Zero-PII チェック・pytest を通して push、draft PR 作成 | 完了 |

### 3.2 人手が必要（実機・アカウント操作。クラウドからは実施不可）

| # | タスク | 備考 |
|---|---|---|
| H1 | 一本化 PR #2（テスト・PLAN・ドキュメント整合）をマージ | PR #1/#3 はマージ済み |
| H2 | リポジトリが **Public** で閲覧できることをシークレットウィンドウで確認 | CLAUDE.md の公開予定日は 2026-11-01 |
| H3 | 旧リポジトリ `pai-so101-final-project` をアーカイブ（Settings → Archive） | 非公開のまま。以後は使わない |
| H4 | （任意）`ci/roboops_ci.yml` を `.github/workflows/` に移して GitHub Actions を有効化 | workflow 権限のあるトークンが必要 |
| H5 | YouTube: タイトル `PAI最終課題_cal29292929`、限定公開以上、1〜3分、倍速使用時は明記 | `SUBMISSION_CHECKLIST.md` §4 |
| H6 | Omnicampus の2箇所に PDF・GitHub URL・YouTube URL を提出 | 締切 11/02 10:00 JST |
| H7 | ACT 自律動作（PR #3 で実施）の結果を `log_work.py` で作業ログに記録。提出後は常駐アプリ停止・GPU 環境で再評価 | 提出物は差し替えない。記録のみ |

## 4. 実機パイプライン（キャットフード移し替え）の現状

- データ: テレオペ 30 エピソード（約 17,900 フレーム、手首カメラ 640x480@30fps）
- 学習: LeRobot ACT（CPU、1000 steps まで実施）
- 自律動作: `lerobot-rollout`（episodic）で実施済み（PR #3）。`win_eval_catfood.ps1` は手首カメラ index を `-WristCam` で切替可能
- 次の改善候補（提出後）: GPU での追加学習（6000 steps 以上）、自律動作の成功率評価、データ拡充

## 5. 自律動作の安全機構（`scripts/safe_rollout.py`、実機未検証）

実機観察（開始姿勢が赤皿のキブル内／リセット位置が赤皿の右上／把持がぎくしゃくして皿の底・縁に接触／エピソード2で30秒停止）への対策:

| 対策 | 内容 | 主な引数 |
|---|---|---|
| ホーム復帰 | 開始時・各リセット時・終了時に `configs/home_pose_catfood.yaml`（青皿の真上）へ。①shoulder_lift/elbow_flex だけで持ち上げ → ②pan 等。終了後もトルク保持 | `--home-speed` 8 deg/s |
| 平滑化 | ポリシー出力に指数移動平均。エピソード開始時は現在姿勢から始める | `-EmaAlpha` 0.3 |
| 高さ下限 | `configs/floor_pose_catfood.yaml`（皿の底すれすれ）より下がる側へ shoulder_lift/elbow_flex を行かせない（関節ごとの近似） | `--save-floor` で記録 |
| 停止検知 | 全関節の変化 1° 未満が 4 秒続いたらエピソード打ち切り → ホーム復帰 | `-StallSec` 4 |
| 速度・可動域 | 1ステップ最大 5°、関節角は設定可動域の 0.8 倍 | `-MaxRelTarget` 5 / `-LimitScale` 0.8 |

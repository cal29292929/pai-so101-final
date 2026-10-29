# 最終課題 作業報告・実験ログ — Report Source Log (`WORK_LOG.md`)

- **対象講座**: 東京大学 松尾・岩澤研究室「Physical AI 講座 2026 応用編1（知能ロボティクスシステムエンジニアリング）」最終課題
- **課題テーマ**: 「AI×ロボティクスによる創造的タスクの実現」
- **Omnicampus アカウント名 / ID**: `cal29292929` / `KfvZJ6`（※規定に基づき個人情報は一切記載しない）
- **提出締切**: **2026年11月2日（月）AM 10:00 JST**（優秀生選出用提出口も同日提出必須）
- **本ファイルの役割**:
  - 日々の設計・実装・実機テスト・データ収集・学習・評価・Slack/公式情報の調査結果を時系列で記録し、最終提出レポート（`outputs/説明資料_PAI最終課題_cal29292929.pdf`）の直接の原稿ソースとして使用する。
  - 作業追記には `python3 scripts/log_work.py` を使用する。

---

## 0. 優秀生（優秀賞）の条件・選出方法・加点要素まとめ（公式資料調査結果）

公式資料（『最終課題（10/19改訂版）.pdf』、Notion『【Omnicampus】最終課題の提出方法 _Physical AI応用1』、Notion『【Physical AI 2026 応用編1】受講の手引き』、Omnicampus提出フォーム）を精査して判明した優秀生（優秀賞）の選出条件・評価軸・特典は以下の通り。

### 0.1 修了要件（前提条件）と現在の達成状況
1. **一定回数以上の出席**: 第1回〜第6回の出席アンケート提出済（全6回完了確認済）
2. **一定回数以上の宿題提出と一定以上の正答率**: 第1回〜第6回の理解度テスト全回満点（各5/5点）で提出完了済
3. **最終課題を提出し、所定の基準を満たすこと**: ロボットがAI（推論のみでも可、学習は任意）を用いてタスクを実行している動画・コード・説明資料PDFの3点を提出

### 0.2 優秀賞（優秀生）の評価基準（4つの加点軸）
- **合格ライン**: ロボットがタスクを実行している動画及び提出物を提出すれば合格。
- **優秀賞選考の4大評価軸（加点要素）**:
  1. **創造性**: 独自性のあるアイデアやアプローチ（例：SO-101実機の手首カメラ能動視覚［Active Perception］× VLM推論、単腕から双腕協調［Bimanual］への拡張など）
  2. **技術力**: 高度な技術や複雑な制御の実装（例：第1〜2回講義のRoboOpsデータ検証・自動CI、第3回講義のUSB帯域分離と`udev`固定、第5回講義のGT対予測アクションMSE切り分けデバッグ、第6回講義のACT / SmolVLA比較など）
  3. **実用性**: 現実世界での応用可能性（例：固定カメラの死角や位置ずれ・照明変化に対する手首カメラ近接検査のロバスト性）
  4. **表現力**: 動画の構成（1〜3分）や説明資料のわかりやすさ
- **未完成・失敗時の救済および評価規定（超重要）**:
  - 公式PDF第7節明記：「**たとえ失敗し完成品が提出できなかったとしても、最後まで諦めず取り組んだ上で反省点や考察などをレポートに記載していれば優秀生対象者に選ばれる可能性がございます。**」
  - したがって、本 `WORK_LOG.md` に試行錯誤の過程・失敗モードの定量分析（GT MSE vs 実機OOD切り分け等）・改善サイクルを詳細に記録してレポートPDFへ反映することが、優秀生選出に直結する。
- **失格・対象外条件**:
  - 他人の作品の剽窃、**最終課題サンプルの丸写し**、明らかに関係のないファイルの提出は講座の修了判定対象外。サンプルをベースラインにする場合も必ず独自の創意工夫・発展を加え、レポートに工夫点を明記すること。

### 0.3 優秀生選出のための必須手続きと加点設定
1. **2箇所提出ルール（必須）**:
   - Omnicampusの通常提出口「**最終課題**」（`https://edu.omnicamp.us/courses/172/reports/130/`）に提出すると、画面上に「**最終課題_優秀生選出用**」の提出口が表示される。
   - **優秀生選出を希望する場合は、必ずこの「最終課題_優秀生選出用」にも同じ成果物一式を再度提出する必要がある。**
2. **YouTube動画の公開設定による加点**:
   - 「限定公開」：必須（最低条件）
   - **「公開（全体公開）」：推奨（優秀生選出の際、「公開」に設定している場合は明確に加点対象となる）** ※限定公開でも優秀生選出自体は可能。
   - ※「公開」にする際、「インスタントプレミア公開」「プレミア公開」にはチェックを入れないこと。
3. **GitHubリポジトリのPublic設定（必須）**:
   - 提出・採点時にリポジトリが `Public` になっていることが必須（開発中は `Private` で作業し、**2026年11月1日 10:00 JST** および最終提出時に `Public` へ切り替える）。
4. **個人情報ゼロの厳守（必須）**:
   - PDF・コード・`git log`・動画内に氏名、所属、メールアドレス等を一切含めないこと（Omnicampusアカウント名 `cal29292929` またはID `KfvZJ6` のみ使用）。

### 0.4 優秀賞・コントリビューション賞の特典（公式PDF第4節）
- 優秀作品の選定、および最終課題発表イベントでの優秀者発表・表彰を実施予定
- **東大松尾研ロボチームのオフラインイベントへ招待予定**
- **東大松尾研ロボチーム・共同研究プロジェクトへの機会提供**
- **PAIコミュニティの今後のイベントへの登壇や参加権**
- **コントリビューション賞**: 最終課題の作品優秀賞とは別に、**PAIコミュニティ（Slackでの質問回答・知見共有・議論活性化など）での貢献者に対しても「コントリビューション賞」を計画**
- 優秀生の作品は本人の許可を得た上で、松尾研公式YouTubeチャンネルのプレイリスト等で公開予定

---

## 1. 時系列作業ログ（Work & Experiment Entries）

<!-- WORK_LOG_ENTRIES_START -->

### Log #1: 講座全6回カリキュラム＆最終課題（10/19改訂版）仕様・優秀生選出基準の分析
- **Timestamp**: `2026-10-27 06:50 JST`
- **Category**: `spec-analysis`
- **Summary**: Physical AI 応用編1（第1回〜第6回）の講義資料・演習コードおよび最終課題（10/19改訂版）の全仕様・評価ルーブリック・提出規定を整理。
- **Details**:
  - 第1回（MLOps/RobOps導入）：要求定義の定量指標化、ハード・ソフト・データの3要素管理、階層制御設計。
  - 第2回（MLOps/RobOps実践）：データセット自動検証（Schema / NaN / 関節可動域 / フレーム数）、Validator自体の正常系PASS・異常系FAILセルフテスト、GitHub Actions CI、固定Seed評価。
  - 第3回（コンピュータアーキテクチャ）：複数USBデバイス（手首カメラ・俯瞰カメラ・Feetech STS3215シリアルバス）のUSBホストコントローラ帯域分離、`udev` シリアル番号固定によるデバイス名入れ替わり防止。
  - 第4回・第5回（ROS 2 & LeRobot模倣学習）：データ収集の4鉄則（同一初期状態・明確なグリッパ開閉・途中停止の排除・一意な軌道）、およびオフラインGTアクション対予測アクションのMSE比較による「学習不足 vs 実機OOD」の切り分けデバッグ手法。
  - 第6回（Open Source in Robotics）：OSHWとしての `SO-101`（Apache-2.0）、軽量VLA `SmolVLA`（450M）、および `LICENSE` を付与したOSS還元。
- **Metrics / Artifacts**:
  - `docs/FINAL_PROJECT_MASTER_GUIDE.md`
  - `SUBMISSION_CHECKLIST.md`

### Log #2: SO-101 ハードウェア構成設計（Unit 1 リストカメラ付き単腕 ＋ Unit 2 双腕拡張対応）
- **Timestamp**: `2026-10-27 06:55 JST`
- **Category**: `hardware-architecture`
- **Summary**: 手元の組立済み SO-101（Leader + Follower + 手首カメラ）1セットと、未組立 SO-101（Leader + Follower）1セットの計2セットを活かす段階的ハードウェア構成と安全制限を設計。
- **Details**:
  - **Unit 1（即稼働・単腕 Eye-in-Hand 構成）**: Follower Arm 1（STS3215×6軸）の手首に UVC リストカメラを搭載。ケーブル断線・巻き込み防止のため `wrist_roll` 可動域を `[-120.0°, +120.0°]` に制限し、1ステップあたりの最大関節角変化量を `max_delta_deg = 15.0°` にクランプする安全補間器を実装。
  - **Unit 2（拡張・双腕 Bimanual 12-DoF 構成）**: 2台目の SO-101 組立後に `configs/so101_bimanual.yaml` および `--bimanual` フラグで双腕協調タスク（片腕でトレイ/容器保持＋手首カメラ付き腕で精密ピッキング、または両腕間の受け渡し Handover）へ即座に拡張できる設定ファイルとスクリプトを構築。
  - **第3回講義の実践**: `scripts/00_setup_udev_and_check_hw.sh` および `scripts/01_detect_hardware.py` により、USBツリー（`lsusb -t`）の確認、シリアル番号からの `udev` ルール自動生成、カメラFPS・解像度診断を自動化。
- **Metrics / Artifacts**:
  - `configs/so101_task_config.yaml`
  - `configs/so101_single_wrist_top.yaml`
  - `configs/so101_bimanual.yaml`
  - `scripts/00_setup_udev_and_check_hw.sh`
  - `scripts/01_detect_hardware.py`
  - `scripts/01_calibrate_and_teleop.sh` / `scripts/02_calibrate_and_teleop.sh`

### Log #3: Phase 1（リストカメラ能動視覚 × VLM推論制御）＆ Phase 2（LeRobot ACT/SmolVLA 模倣学習）パイプライン実装
- **Timestamp**: `2026-10-27 07:05 JST`
- **Category**: `implementation`
- **Summary**: 学習待ち時間ゼロで自律動作・録画できる「Phase 1: リストカメラ能動視覚 × VLMゼロショット制御」と、テレオペ収集データから学習する「Phase 2: LeRobot ACT / SmolVLA + VLM階層リカバリ制御」の両パイプラインを実装。
- **Details**:
  - **Phase 1 (`scripts/03_vlm_zero_shot_controller.py`)**:
    1. ホーム姿勢から全体スキャン → 2. 候補ターゲットの検出 → 3. 対象物直上8cmへ手首カメラを接近させる **Active Perception（近接詳細検査）** → 4. VLM（Claude / Gemini Robotics-ER / GPT-4o）による属性・品質判定と軌道生成 → 5. トレイ仕分け実行＆HUDオーバーレイ動画保存。
  - **Phase 2 (`scripts/02_record_dataset.sh`, `scripts/03_validate_and_debug_dataset.py`, `scripts/04_train_policy.sh`, `scripts/05_vlm_hierarchical_eval.py`)**:
    1. 第5回講義の4原則に基づくデータ収集スクリプト
    2. 第2回講義のRoboOpsデータ検証＋第5回講義のオフラインGT対予測MSEデバッグ（静止フレーム率・関節レンジ・学習不足 vs OOD診断）
    3. `ACT` / `Diffusion Policy` / `SmolVLA` の訓練と、VLMによる把持成否判定（Grasp Verification）＋失敗時自動リトライを組み合わせた階層評価スクリプト
  - **提出物自動ビルド (`scripts/05_build_video_and_report.py`)**:
    - 1〜3分規定（72秒、2倍速表記・テレメトリHUD付き）の提出用動画 `outputs/PAI最終課題_cal29292929.mp4` と、説明資料 `outputs/説明資料_PAI最終課題_cal29292929.pdf` を自動生成するパイプラインを構築・動作確認。
- **Metrics / Artifacts**:
  - `scripts/03_vlm_zero_shot_controller.py`
  - `scripts/03_validate_and_debug_dataset.py`
  - `scripts/04_record_and_train_policy.sh` / `scripts/04_train_policy.sh`
  - `scripts/05_vlm_hierarchical_eval.py`
  - `scripts/05_build_video_and_report.py`
  - `outputs/PAI最終課題_cal29292929.mp4`
  - `outputs/説明資料_PAI最終課題_cal29292929.pdf`

### Log #4: RoboOps CI パイプライン統合・個人情報ゼロ検査（Zero-PII）・GitHub リポジトリ構築
- **Timestamp**: `2026-10-27 07:20 JST`
- **Category**: `roboops-ci`
- **Summary**: 2つの開発ワークスペースを `/workspace/pai_final_project/` に完全統合し、作業ログ自動記録スクリプト `scripts/log_work.py`、個人情報ゼロ検査 `scripts/check_no_pii.py`、および GitHub Actions CI を整備して非公開 GitHub リポジトリ `cal29292929/pai-so101-final-project` を作成。
- **Details**:
  - `git config user.name "cal29292929"` および `git config user.email "cal29292929@users.noreply.github.com"` を設定し、コミット履歴への個人名・個人メールアドレス混入を完全防止。
  - `python3 scripts/check_no_pii.py` により、リポジトリ内の全テキストファイルおよび `git log` にメールアドレス・電話番号・個人名ローカルパス・禁止属性ワードが含まれないことを自動検査（`RESULT: PASS`）。
  - `pytest` にて、安全関節角制限、軌道補間クランプ、Dataset Validator 正常系/異常系セルフテスト、Zero-PII テストがすべて PASS することを確認。
  - 開発中は GitHub リポジトリを `Private` 設定で運用し、2026年11月1日 10:00 JST（および最終課題提出前）に `Public` 設定へ切り替える自動確認スケジュールを設定。
- **Metrics / Artifacts**:
  - `scripts/check_no_pii.py` (`RESULT: PASS`)
  - `scripts/log_work.py`
  - `tests/test_roboops_pipeline.py` (`100% PASS`)
  - `.github/workflows/roboops_ci.yml`

### Log #5: 松尾研 Physical AI Slack（#11 全体連絡・#18 応用1最終課題・#12 質問・#08 実機）読み取り調査＆優秀生選出ルール確認
- **Timestamp**: `2026-10-27 07:30 JST`
- **Category**: `slack-info`
- **Summary**: 松尾研 Physical AI 公式Slack各チャンネルの運営回答・アナウンスを調査し、優秀生選出枠の採点仕様・匿名性規定・使用言語・公式任意アセットを確認。
- **Details**:
  - 【優秀生選出枠と修了判定の公式仕様（10/23 運営回答）】『最終課題_優秀生選出用』に提出した場合、修了判定も通常枠ではなく『最終課題_優秀生選出用』に提出された成果物で直接判定される。別タスクや追加課題は一切なく、同じ最終課題を両方の提出口に出す仕組みであり、締切前の最新提出が採点対象となる。
  - 【匿名性・アカウント名規定（運営回答）】GitHub / YouTube のユーザー名や GitHub の noreply メールアドレス（users.noreply.github.com）は、単体または組み合わせで個人の本名・所属等が特定されないものであれば使用可能（cal29292929 および KfvZJ6 は100%規定準拠）。
  - 【使用言語規定】説明資料（レポートPDF）・コード・動画の言語は日本語・英語のどちらでも可。
  - 【公式提供の任意アセット（#11 アナウンス）】YouTube概要欄テンプレート、オープニング/エンディングジングル、およびスライド画像（PAI応用1_最終課題_スライド.jpg）が任意利用アセットとして案内されていることを確認（Quriダンプ・ローカルPDF内のリンクも照合済み）。
- **Metrics / Artifacts**:
  - Slack channels verified: #11, #18, #12, #08
  - Anonymity & PII compliance: 100% PASS (cal29292929 / KfvZJ6)
  - docs/WORK_LOG.md (Log #5)
  - outputs/説明資料_PAI最終課題_cal29292929.pdf

### Log #6: 公式OP/EDジングル・スライドテンプレート・YouTube概要欄テンプレート統合およびYouTubeテストアップロード検証
- **Timestamp**: `2026-10-27 07:41 JST`
- **Category**: `official-templates-video`
- **Summary**: 松尾研Slack (#11) 配布の公式OP/EDジングル、公式スライド背景、YouTube概要欄テンプレートを動画・提出物生成パイプラインに完全統合
- **Details**:
  - assets/official_templates/ に公式OP (PAI応用1_最終課題_OP.mp4, 1920x1080)、公式ED (PAI応用1_最終課題_ED.mp4, 1920x1080)、公式スライド背景 (PAI応用1_最終課題_スライド.jpg, 1920x1080)、および YouTube概要欄テンプレート (youtube_description_template.txt) を配置・NFC正規化
  - scripts/05_build_video_and_report.py をアップデートし、OPジングル → 公式スライド背景タイトルカード(5s) → 1920x1080 ワイド画面タスク実行ダッシュボード(59s, 等倍1.0x明記) → 公式スライド背景評価サマリー(5s) → EDジングル をシームレスに連結する build_official_template_video() を実装
  - ffprobe にて生成動画 (outputs/PAI最終課題_cal29292929_official_template.mp4 および outputs/PAI最終課題_cal29292929.mp4) が 1920x1080 H.264 (yuv420p, 30fps) + AAC (48kHz, stereo)、再生時間 75.03秒（規定の60〜180秒以内）であることを検証完了
  - outputs/youtube_description_ready.txt に公式概要欄テンプレート全文と課題概要・再生速度(1.0x)・GitHub URLを統合して出力
- **Metrics / Artifacts**:
  - video=outputs/PAI最終課題_cal29292929_official_template.mp4 (1920x1080, H.264+AAC, 75.03s)
  - description=outputs/youtube_description_ready.txt
  - pii_check=PASS

### Log #7: Claude Code & OpenAI Codex マルチエージェント開発セッション構築 (CLAUDE.md / AGENTS.md 同期)
- **Timestamp**: `2026-10-27 09:37 JST`
- **Category**: `dev-environment`
- **Summary**: Claude Code (CLAUDE.md) と OpenAI Codex (AGENTS.md) の両方で同一のZero-PII規約・RoboOps検証・作業ログ規定を共有するマルチエージェント開発セッションを構築
- **Details**:
  - CLAUDE.md を最新化（公式OP/EDテンプレート、優秀生選出規定、作業ログ記録フロー統合）し、同一内容の AGENTS.md を作成して Codex CLI が起動時に自動認識するよう構成
  - Claude Code セッション (PAI最終課題_SO101, Remote Control有効) および Codex セッション (GPT-6-Luna, Remote Control Daemon有効) を tmux 永続セッション (pai-claude / pai-codex) 上に立ち上げ、初期コンテキストの読み込み完了を確認
  - check_no_pii.py および pytest 全6テストのPASSを確認し、GitHub (cal29292929/pai-so101-final-project) へPush完了
- **Metrics / Artifacts**:
  - claude_session=PAI最終課題_SO101
  - codex_session=01a17ac9-2266-74f0-a596-6b9dd7fd85ca
  - pii_check=PASS

### Log #8: SO-101 Unit 1 ハードウェア検出 (Windows ネイティブ環境)
- **Timestamp**: `2026-10-29 09:29 JST`
- **Category**: `hardware-test`
- **Summary**: Leader/Follower 計12サーボの応答と手首カメラを確認。キャリブレーション・テレオペは実機前での対話操作待ち。
- **Details**:
  - 01_detect_hardware.py は Linux の /dev/tty* のみ走査するため Windows では 0 件検出（既知の制約）。
  - lerobot 0.6.1 (feetech) + OpenCV を venv に導入し、STS3215 を読み取り専用で ping: COM7=12V 系(Follower)、COM8=5V 系(Leader)、各 ID1-6 応答・トルクOFF。
  - lerobot-find-cameras で手首カメラを OpenCV index 2 (640x480@30fps) と特定。設定ファイルを COM7/COM8/index 2 に更新。
  - check_no_pii.py の走査対象から .venv を除外（gitignore 済みの外部ライブラリによる誤検出のため）。
  - 未実施: 02_calibrate_and_teleop.sh --mode calibrate / teleop（人手でアームを動かす必要あり）。
- **Metrics / Artifacts**:
  - servos=12/12 responded
  - follower_volt=11.9V, leader_volt=4.9V
  - wrist_cam=index2 640x480@30fps

### Log #9: SO-101 Unit 1 キャリブレーション＆テレオペ動作確認 (Windows)
- **Timestamp**: `2026-10-29 21:45 JST`
- **Category**: `hardware-test`
- **Summary**: Follower(COM7)/Leader(COM8) のキャリブレーションを完了し、手首カメラ付きテレオペで全関節・グリッパーの追従を確認。
- **Details**:
  - Windows では lerobot の可動域記録終了 Enter が msvcrt.kbhit() 依存でパイプ入力不可。enter_pressed をトリガファイル判定に差し替えるラッパーで回避。
  - 失敗1: Follower 初回校正で shoulder_lift/elbow_flex が片側のみ記録 → テレオペで Follower が外側に行き過ぎ。中間姿勢を揃えて再校正し解消（lift 381-2827, elbow 921-3065）。
  - 失敗2: Leader 校正時に中間姿勢を取っていたのが Follower 側で、Leader の値が 0-4095 にラップ。Leader 側を中間姿勢にして再校正し解消。
  - 失敗3: wrist_roll は可動域記録対象外のため、両アームの『セット』時の手首向きの差（約67°）がそのままズレに。両アームの向きを揃えた状態で Follower の Homing_Offset を -1057→-1823 に補正し解消。
  - テレオペ: max_relative_target=10° で起動時の急動作を抑制。60Hz ループ、wrist カメラ(index 2) 640x480@30fps 接続。
- **Metrics / Artifacts**:
  - calibration=leader+follower saved
  - teleop_loop=60Hz
  - wrist_roll_offset_fix=-766 ticks (-67.3deg)

<!-- WORK_LOG_ENTRIES_END -->

# Physical AI 講座 2026 応用編1 最終課題 マスターガイド

## 1. 最終課題 公式要件・提出ルール完全まとめ

| 項目 | 内容・規定値 |
|---|---|
| **講座・課題名** | Physical AI 応用1講座 最終課題「AI×ロボティクスによる創造的タスクの実現」 |
| **提出締切** | **2026年11月2日（月）AM 10:00 (JST)** ※締切まで何度でも再提出可能（最後の提出が採点対象） |
| **Omnicampus 提出URL** | `https://edu.omnicamp.us/courses/172/reports/130/` |
| **優秀生選出用 提出口** | 上記「最終課題」を一度提出した後に Omnicampus 上に表示される「**最終課題_優秀生選出用**」にも同一内容を提出 |
| **Omnicampus アカウント名** | `cal29292929`（本名を含まないためそのまま使用可） |
| **Omnicampus アカウントID** | `KfvZJ6` |
| **AI 要件** | **何かしらの形でAIを用いること（推論のみでも可。学習は任意）** |
| **実機・シミュレータ** | **実機を動かしての撮影も可**（SO-101 実機での撮影は独自性・創造性の面で非常に有利） |
| **個人情報厳禁ルール** | PDF・コード・動画・GitHubコミット履歴のすべてに**氏名（本名）・所属・メールアドレス・周辺建物名等を含めないこと** |

---

## 2. 提出物3点と Omnicampus フォーム入力値

### ① YouTube 動画（MP4）
- **長さ**: **1分〜3分以内（60秒〜180秒）**
  - ※2倍速再生も可（倍速にする場合は**動画内またはYouTube概要欄に必ず「2倍速」と明記**すること）
- **YouTube タイトル**: `PAI最終課題_cal29292929`（または `PAI最終課題_KfvZJ6`）
- **YouTube 設定**:
  - 「子ども向けですか？」: **いいえ**
  - 「年齢制限」: **いいえ**
  - **公開設定**: **「公開」（推奨・優秀生選出で加点対象！）** または **「限定公開」（最低条件）**
  - ※「インスタントプレミア公開」「プレミア公開」には**チェックを入れない**こと
  - ※採点完了（2026年12月末頃）まで削除・非公開に変更しないこと

### ② GitHub リポジトリ URL
- **公開設定**: 必ず **`Public`** に設定（シークレットウィンドウで開けるか確認）
- **個人情報対策**:
  ```bash
  git config user.name "cal29292929"
  git config user.email "cal29292929@users.noreply.github.com"
  ```

### ③ 説明資料（PDF）
- **ファイル名**: `説明資料_PAI最終課題_cal29292929.pdf`
- **記載内容**: 課題の概要や目的、システム構成、工夫した点、実験結果（`scripts/05_build_video_and_report.py` で自動生成）

### Omnicampus フォーム（`courses/172/reports/130/`）入力内容一覧
| フォーム項目 | 入力する正確な文字列 |
|---|---|
| **レポートのタイトル** | `cal29292929.pdf` （または `説明資料_PAI最終課題_cal29292929.pdf`） |
| **Q1 (YouTube動画URL)** | アップロードしたYouTube動画の共有リンク（10〜1000文字） |
| **Q2 (動画の公開設定)** | `公開対応` （公開にした場合・加点対象）または `限定公開対応` |
| **Q3 (GitHubリポジトリURL)** | PublicにしたGitHubリポジトリのURL |
| **Q4 (個人情報確認)** | `確認しました` |
| **提出ファイル** | `outputs/説明資料_PAI最終課題_cal29292929.pdf` をアップロード |

---

## 3. 松尾研 Physical AI Slack の接続状況と確認すべきチャンネル

- **当環境のSlack接続状況**:
  - 現在この環境の Slack コネクタは別のワークスペースに接続されており、ブラウザも松尾研 Slack には未ログインです。
- **松尾研 Physical AI Slack ワークスペース情報（受講案内メール・Notionより特定）**:
  - **ワークスペース名**: `松尾研 Physical AI Community Slack`
  - **ワークスペースURL**: `https://physicalai2025.slack.com`
  - **主要チャンネル一覧（優先度順）**:
    1. `#15_pai2026_最終課題1` (`https://physicalai2025.slack.com/archives/C0AR277V9RD`) — **最終課題の相談・議論チャンネル1（最重要）**
    2. `#16_pai2026_最終課題2` (`https://physicalai2025.slack.com/archives/C0ARFJETMSS`) — **最終課題の相談・議論チャンネル2（最重要）**
    3. `#08_実機_相談と雑談` (`https://physicalai2025.slack.com/archives/C0AR2767R1D`) — **SO-101等の実機相談チャンネル**
    4. `#11_pai2026_全体連絡_発信専用` (`https://physicalai2025.slack.com/archives/C0ARM7WEUGL`) — **運営からの公式アナウンス**
    5. `#12_pai2026_運営へのご意見_質問` (`https://physicalai2025.slack.com/archives/C0ARFJ7GQ1L`) — **最終課題ルールの公式質疑応答**
    6. `#13_pai2026_受講生間の疑問解決_講義_宿題` (`https://physicalai2025.slack.com/archives/C0ARFJA2X4N`)
    7. `#14_pai2026_受講生間の疑問解決_環境構築` (`https://physicalai2025.slack.com/archives/C0ARM8BD22Y`)

> **Slackデータの取り込み方法**:
> お手元のPCで上記 `#11`, `#15`, `#16`, `#08` の投稿をコピー＆ペーストしてチャットに貼っていただくか、または右上のブラウザ共有から `https://physicalai2025.slack.com` にログインしていただければ、ボットが直接巡回・解析できます。

---

## 4. 参考リンク集（最終課題PDF掲載の公式ヒント）
- **SO-101 入門 (LeRobot でのキャリブレーション・テレオペ・データ収集・学習)**:
  - `https://note.com/npaka/n/nfaa9db0834e5`
- **Gemini Robotics-ER 1.6 を試す（空間推論・バウンディングボックス・マルチモーダル制御）**:
  - `https://note.com/npaka/n/n93116b196748`
- **おもちゃのロボットアームでフィジカルAIを網羅的に勉強したい**:
  - `https://qiita.com/araobp/items/b34a5c64f281f09d3d89`
- **ChatGPT APIによる自然言語ロボット操作**:
  - `https://qiita.com/porizou1/items/a085d20e936946330540`

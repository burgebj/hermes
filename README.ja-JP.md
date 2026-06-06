<p align="center">
  <img src="assets/banner.png" alt="Hermes Agent" width="100%">
</p>

# Hermes Agent ☤

<p align="center">
  <a href="https://hermes-agent.nousresearch.com/docs/"><img src="https://img.shields.io/badge/Docs-hermes--agent.nousresearch.com-FFD700?style=for-the-badge" alt="Documentation"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://github.com/NousResearch/hermes-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://nousresearch.com"><img src="https://img.shields.io/badge/Built%20by-Nous%20Research-blueviolet?style=for-the-badge" alt="Built by Nous Research"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/Lang-English-blue?style=for-the-badge" alt="English"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-中文-red?style=for-the-badge" alt="中文"></a>
</p>

**[Nous Research](https://nousresearch.com)が構築した、自己改善型のAIエージェントです。** 学習ループを組み込んだ唯一のエージェントであり、経験からスキルを生成し、使用中にそれらを改善し、自身に知識の永続化を促し、過去の会話を自ら検索し、セッションをまたいであなたという人物への理解を深めていきます。月5ドルのVPSでも、GPUクラスタでも、アイドル時にはほぼゼロコストのサーバーレス基盤でも動作します。ノートPCに縛られることはなく、Telegramから話しかけている間にクラウドVM上で作業を進めさせることもできます。

どんなモデルでも使用できます — [Nous Portal](https://portal.nousresearch.com)、[OpenRouter](https://openrouter.ai)（200以上のモデル）、[NVIDIA NIM](https://build.nvidia.com)（Nemotron）、[Xiaomi MiMo](https://platform.xiaomimimo.com)、[z.ai/GLM](https://z.ai)、[Kimi/Moonshot](https://platform.moonshot.ai)、[MiniMax](https://www.minimax.io)、[Hugging Face](https://huggingface.co)、OpenAI、または独自のエンドポイント。`hermes model`で切り替え可能 — コード変更もロックインも不要です。

<table>
<tr><td><b>本格的なターミナルインターフェース</b></td><td>マルチライン編集、スラッシュコマンドの自動補完、会話履歴、割り込みとリダイレクト、ストリーミングツール出力に対応したフル機能のTUI。</td></tr>
<tr><td><b>あなたのいる場所で動く</b></td><td>Telegram、Discord、Slack、WhatsApp、Signal、CLI — すべて単一のゲートウェイプロセスから。ボイスメモの文字起こし、プラットフォームをまたいだ会話の継続性。</td></tr>
<tr><td><b>閉じた学習ループ</b></td><td>エージェント自身が管理し、定期的にナッジを行うメモリ。複雑なタスク完了後の自律的なスキル生成。使用中に自己改善するスキル。LLM要約を活用したクロスセッション想起のためのFTS5セッション検索。<a href="https://github.com/plastic-labs/honcho">Honcho</a>による弁証法的ユーザーモデリング。<a href="https://agentskills.io">agentskills.io</a>のオープン標準と互換。</td></tr>
<tr><td><b>スケジュール自動化</b></td><td>任意のプラットフォームへの配信に対応した、組み込みcronスケジューラ。日次レポート、深夜バックアップ、週次監査 — すべて自然言語で指示し、無人で実行できます。</td></tr>
<tr><td><b>委譲と並列化</b></td><td>独立したサブエージェントを生成し、並列ワークストリームを実行。RPC経由でツールを呼び出すPythonスクリプトを書くことで、複数ステップのパイプラインをコンテキストコストゼロのターンに圧縮します。</td></tr>
<tr><td><b>ノートPCだけでなく、どこでも動作</b></td><td>7つのターミナルバックエンド — local、Docker、SSH、Singularity、Modal、Daytona、Vercel Sandbox。DaytonaとModalはサーバーレス永続性を提供し、エージェントの環境はアイドル時に休止し、必要に応じて目覚めるため、セッション間のコストはほぼゼロです。月5ドルのVPSでもGPUクラスタでも動かせます。</td></tr>
<tr><td><b>研究にすぐ使える</b></td><td>バッチでの軌跡生成、Atropos強化学習環境、次世代のツール呼び出しモデル訓練のための軌跡圧縮。</td></tr>
</table>

---

## クイックインストール

### Linux、macOS、WSL2、Termux

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

### Windows（ネイティブ、PowerShell） — アーリーベータ

> **ご注意:** Windowsネイティブサポートは**アーリーベータ**です。インストールと動作は確認できていますが、Linux/macOS/WSL2と同等のテストはまだ行われていません。問題が発生した場合は[Issueを起票](https://github.com/NousResearch/hermes-agent/issues)してください。現時点でもっとも実績のあるWindowsセットアップは、**WSL2**内で上記のLinux/macOS用ワンライナーを実行する方法です。

PowerShellで以下を実行します:

```powershell
irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex
```

インストーラはすべてを処理します: uv、Python 3.11、Node.js、ripgrep、ffmpeg、**ポータブル版Git Bash**（MinGit、`%LOCALAPPDATA%\hermes\git`に展開 — 管理者権限不要、システムのGitインストールから完全に隔離されます）。Hermesはこのバンドル版Git Bashを使ってシェルコマンドを実行します。

既にGitがインストールされている場合、インストーラはそれを検出して代わりに使用します。なければ約45MBのMinGitをダウンロードするだけで済み — システムのGitに干渉することはありません。

> **Android / Termux:** テスト済みの手動インストール手順は[Termuxガイド](https://hermes-agent.nousresearch.com/docs/getting-started/termux)に記載されています。Termux上では、`.[all]`エクストラがAndroid非対応の音声関連依存を引き込むため、Hermesはキュレートされた`.[termux]`エクストラをインストールします。
>
> **Windows:** Windowsネイティブは**アーリーベータ**としてサポートされています — 上記のPowerShellワンライナーがすべてをインストールしますが、粗削りな部分があり、問題に遭遇したらIssueを起票してください。WSL2（もっとも実績のあるWindows経路）を使いたい場合は、Linuxコマンドがそのまま使えます。Windowsネイティブのインストール先は`%LOCALAPPDATA%\hermes`、WSL2のインストール先はLinuxと同じく`~/.hermes`です。現状でWSL2が必須なHermes機能は、ブラウザベースのダッシュボードチャットペインのみ（POSIX PTYを利用しているため。クラシックCLIとゲートウェイはいずれもネイティブで動作します）。

インストール後:

```bash
source ~/.bashrc    # シェルを再読み込み（または: source ~/.zshrc）
hermes              # 会話開始！
```

---

## はじめに

```bash
hermes              # インタラクティブCLI — 会話を開始
hermes model        # LLMプロバイダとモデルを選択
hermes tools        # 有効にするツールを設定
hermes config set   # 個別の設定値をセット
hermes gateway      # メッセージングゲートウェイを起動（Telegram、Discord等）
hermes setup        # フルセットアップウィザードを実行（一括設定）
hermes claw migrate # OpenClawから移行（OpenClaw利用者の場合）
hermes update       # 最新バージョンへ更新
hermes doctor       # 問題を診断
```

📖 **[完全なドキュメント →](https://hermes-agent.nousresearch.com/docs/)**

## CLIとメッセージングのクイックリファレンス

Hermesには2つのエントリポイントがあります: `hermes`でターミナルUIを起動するか、ゲートウェイを起動してTelegram、Discord、Slack、WhatsApp、Signal、Emailから対話します。会話が始まれば、多くのスラッシュコマンドは両インターフェースで共通です。

| アクション | CLI | メッセージングプラットフォーム |
|---------|-----|---------------------|
| 会話を開始 | `hermes` | `hermes gateway setup` + `hermes gateway start`を実行し、ボットにメッセージを送信 |
| 新しい会話を開始 | `/new` または `/reset` | `/new` または `/reset` |
| モデルを変更 | `/model [provider:model]` | `/model [provider:model]` |
| パーソナリティを設定 | `/personality [name]` | `/personality [name]` |
| 直前のターンを再試行・取り消し | `/retry`、`/undo` | `/retry`、`/undo` |
| コンテキスト圧縮 / 使用量確認 | `/compress`、`/usage`、`/insights [--days N]` | `/compress`、`/usage`、`/insights [days]` |
| スキルを参照 | `/skills` または `/<skill-name>` | `/<skill-name>` |
| 現在の作業を中断 | `Ctrl+C` または新規メッセージ送信 | `/stop` または新規メッセージ送信 |
| プラットフォーム固有のステータス | `/platforms` | `/status`、`/sethome` |

完全なコマンド一覧は[CLIガイド](https://hermes-agent.nousresearch.com/docs/user-guide/cli)と[メッセージングゲートウェイガイド](https://hermes-agent.nousresearch.com/docs/user-guide/messaging)を参照してください。

---

## ドキュメント

すべてのドキュメントは**[hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/)**にあります:

| セクション | 内容 |
|---------|---------------|
| [クイックスタート](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart) | インストール → セットアップ → 2分で最初の会話 |
| [CLIの使い方](https://hermes-agent.nousresearch.com/docs/user-guide/cli) | コマンド、キーバインド、パーソナリティ、セッション |
| [設定](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) | 設定ファイル、プロバイダ、モデル、全オプション |
| [メッセージングゲートウェイ](https://hermes-agent.nousresearch.com/docs/user-guide/messaging) | Telegram、Discord、Slack、WhatsApp、Signal、Home Assistant |
| [セキュリティ](https://hermes-agent.nousresearch.com/docs/user-guide/security) | コマンド承認、DMペアリング、コンテナ隔離 |
| [ツールとツールセット](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools) | 40以上のツール、ツールセットシステム、ターミナルバックエンド |
| [スキルシステム](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) | 手続き的記憶、Skills Hub、スキルの作成 |
| [メモリ](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) | 永続メモリ、ユーザープロファイル、ベストプラクティス |
| [MCP統合](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) | 任意のMCPサーバーを接続して機能を拡張 |
| [Cronスケジューリング](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron) | プラットフォーム配信付きのスケジュールタスク |
| [コンテキストファイル](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files) | 全会話に影響するプロジェクトコンテキスト |
| [アーキテクチャ](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture) | プロジェクト構造、エージェントループ、主要クラス |
| [コントリビューション](https://hermes-agent.nousresearch.com/docs/developer-guide/contributing) | 開発セットアップ、PRプロセス、コードスタイル |
| [CLIリファレンス](https://hermes-agent.nousresearch.com/docs/reference/cli-commands) | 全コマンドとフラグ |
| [環境変数](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) | 環境変数の完全リファレンス |

---

## OpenClawからの移行

OpenClawからの移行であれば、Hermesは設定、メモリ、スキル、APIキーを自動的にインポートできます。

**初回セットアップ時:** セットアップウィザード（`hermes setup`）は自動的に`~/.openclaw`を検出し、設定開始前に移行を提案します。

**インストール後はいつでも:**

```bash
hermes claw migrate              # インタラクティブ移行（フルプリセット）
hermes claw migrate --dry-run    # 何が移行されるかをプレビュー
hermes claw migrate --preset user-data   # シークレットなしで移行
hermes claw migrate --overwrite  # 既存の競合を上書き
```

インポート対象:
- **SOUL.md** — ペルソナファイル
- **メモリ** — MEMORY.mdとUSER.mdのエントリ
- **スキル** — ユーザー作成スキル → `~/.hermes/skills/openclaw-imports/`
- **コマンド許可リスト** — 承認パターン
- **メッセージング設定** — プラットフォーム設定、許可ユーザー、作業ディレクトリ
- **APIキー** — 許可リストに含まれるシークレット（Telegram、OpenRouter、OpenAI、Anthropic、ElevenLabs）
- **TTSアセット** — ワークスペースの音声ファイル
- **ワークスペース指示** — AGENTS.md（`--workspace-target`使用時）

全オプションは`hermes claw migrate --help`を参照するか、`openclaw-migration`スキルを使用すると、ドライランプレビュー付きのエージェント主導インタラクティブ移行が可能です。

---

## コントリビューション

コントリビューションを歓迎します！開発セットアップ、コードスタイル、PRプロセスについては[コントリビューションガイド](https://hermes-agent.nousresearch.com/docs/developer-guide/contributing)を参照してください。

コントリビュータ向けのクイックスタート — `setup-hermes.sh`でクローンして開始:

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
./setup-hermes.sh     # uvをインストール、venvを作成、.[all]をインストール、~/.local/bin/hermesにシンボリックリンク
./hermes              # venvを自動検出 — 事前の`source`は不要
```

手動手順（上記と同等）:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

> **RLトレーニング（任意）:** RL/Atropos統合（`environments/`） — 完全なセットアップは[`CONTRIBUTING.md`](https://github.com/NousResearch/hermes-agent/blob/main/CONTRIBUTING.md#development-setup)を参照してください。

---

## コミュニティ

- 💬 [Discord](https://discord.gg/NousResearch)
- 📚 [Skills Hub](https://agentskills.io)
- 🐛 [Issues](https://github.com/NousResearch/hermes-agent/issues)
- 🔌 [HermesClaw](https://github.com/AaronWong1999/hermesclaw) — コミュニティ製WeChatブリッジ: 同じWeChatアカウントでHermes AgentとOpenClawを動かせます。

---

## ライセンス

MIT — [LICENSE](LICENSE)を参照。

[Nous Research](https://nousresearch.com)が構築。

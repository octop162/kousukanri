# 工数管理

タイムライン上でドラッグ&ドロップしながら作業時間を記録できるデスクトップアプリ。

![icon](./icon.png)

## 機能

- **タイムライン** — 縦軸が時間。ドラッグで新規作成、ブロックの移動・リサイズ、ダブルクリックで隙間埋め
- **タイマー** — ワンクリックで計測開始。ブロックがリアルタイムに伸びる。開始時に自動で今日に切替
- **プロジェクト** — タスクをプロジェクトごとに色分け管理
- **ルーティン** — 定期タスクをプリセット登録してワンクリック追加
- **一括編集** — 複数タスクを選択して名前・プロジェクトをまとめて変更
- **テーマ** — Dark / Light / Sky / BlackGreen / Monokai / Solarized
- **システムトレイ** — 常時トレイアイコン表示。最小化/閉じるでトレイに格納、多重起動防止
- **API サーバー** — Flask ベースの REST API。設定画面で有効化、外部ツールから HTTP 経由で操作可能
- **Web UI** — React SPA。ブラウザでタスク・プロジェクト・レポートを閲覧・操作
- **CLI** — コマンドラインからタスク追加・レポート表示 (API サーバー経由)
- **API ドキュメント** — OpenAPI 3.0 スペック + ReDoc で閲覧可能
- **データ永続化** — SQLite (`~/.tracker/tracker.db`)

## 起動方法

```bash
kousu-kanri-gui.exe
```

## Web UI

設定画面で「API サーバーを有効にする」をオンにしてアプリを再起動すると、ブラウザで操作できる。

- タスク一覧: http://127.0.0.1:8321/tasks
- プロジェクト: http://127.0.0.1:8321/projects
- 日次レポート: http://127.0.0.1:8321/report
- 期間集計: http://127.0.0.1:8321/reports
- 日別レポート: http://127.0.0.1:8321/reports-by-day
- API ドキュメント: http://127.0.0.1:8321/api/docs

> API 経由でタスクやプロジェクトを追加すると、GUI がリアルタイムで自動更新される（Qt シグナルによるイベント駆動）。

## CLI

API サーバーが起動している状態で使用する。

```bash
# タスク一覧（今日）
kousu-kanri tasks
# 日付指定
kousu-kanri tasks -d 2026-03-10
# タスク追加
kousu-kanri add コーディング 09:00 10:30 -p 開発

# プロジェクト一覧
kousu-kanri projects
# プロジェクト追加
kousu-kanri add-project ミーティング -c "#4CAF50"

# 日次レポート（内訳付き）
kousu-kanri report --detail
# 期間集計
kousu-kanri reports --since 7d
# 日別レポート
kousu-kanri reports-by-day -f 2026-03-01 -t 2026-03-10 --detail
```

共通オプション: `--port PORT` (デフォルト: 8321、環境変数 `KOUSU_PORT`)

## API

```bash
# ヘルスチェック
curl http://localhost:8321/api/health

# タスク一覧
curl http://localhost:8321/api/tasks?date=2026-03-10
# タスク追加
curl -X POST http://localhost:8321/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"name": "コードレビュー", "start": "09:00", "end": "10:30", "project": "開発"}'

# プロジェクト一覧
curl http://localhost:8321/api/projects
# プロジェクト追加
curl -X POST http://localhost:8321/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "ミーティング", "color": "#4CAF50"}'

# レポート
curl "http://localhost:8321/api/report?detail=1"
curl "http://localhost:8321/api/reports?since=7d"
curl "http://localhost:8321/api/reports-by-day?since=30d&detail=1"
```

詳細は [API ドキュメント](http://127.0.0.1:8321/api/docs) (ReDoc) を参照。

## セットアップ

### 開発

```bash
# GUI 起動
uv run python main.py

# Web UI 開発 (ホットリロード、/api は :8321 にプロキシ)
cd web && npm run dev

# CLI (開発時)
uv run python cli.py tasks
```

### ビルド (exe)

[Nuitka](https://nuitka.net/) で Python なしで実行できる exe を生成できる。

```bash
# 1. Web UI ビルド
cd web && npm run build && cd ..

# 2. GUI ビルド (standalone、static/ 同梱)
uv run python -m nuitka --standalone --enable-plugin=pyside6 \
  --windows-console-mode=disable --windows-icon-from-ico=icon.ico \
  --include-data-dir=static/=static/ \
  --output-dir=dist --output-filename=kousu-kanri-gui.exe \
  --assume-yes-for-downloads main.py

# 3. CLI ビルド (standalone)
uv run python -m nuitka --standalone \
  --windows-console-mode=force --windows-icon-from-ico=icon.ico \
  --output-dir=dist --output-filename=kousu-kanri.exe \
  --assume-yes-for-downloads cli.py

# 4. CLI を GUI にマージ (共通 DLL を共有)
cp -r dist/cli.dist/* dist/main.dist/
```

成果物: `dist/main.dist/` に `kousu-kanri-gui.exe` と `kousu-kanri.exe` が同居

> `v*` タグを push すると GitHub Actions で自動ビルド&リリースされる。

### API クライアント再生成

API を変更した場合、OpenAPI スペックを更新してクライアントを再生成する。

```bash
# web/public/openapi.yaml を編集後:
uvx openapi-python-client generate --path web/public/openapi.yaml --output-path cli_client --overwrite
```

## アンインストール

アプリを削除する前に、設定画面の「Windows 起動時に自動起動する」のチェックを外して保存してください。

チェックを外さずに削除した場合は、以下のコマンドでレジストリを手動削除できます。

```bat
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v KousuKanri /f
```

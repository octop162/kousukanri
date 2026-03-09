# 工数管理

タイムライン上でドラッグ&ドロップしながら作業時間を記録できるデスクトップアプリ。

![icon](./icon.png)

## 機能

- **タイムライン** — 縦軸が時間。ドラッグで新規作成、ブロックの移動・リサイズ、ダブルクリックで隙間埋め
- **タイマー** — ワンクリックで計測開始。ブロックがリアルタイムに伸びる。開始時に自動で今日に切替
- **プロジェクト** — タスクをプロジェクトごとに色分け管理
- **ルーティン** — 定期タスクをプリセット登録してワンクリック追加
- **エクスポート** — テキスト形式でクリップボードにコピー
- **テーマ** — Dark / Light / Sky / BlackGreen / Monokai / Solarized
- **一括編集** — 複数タスクを選択して名前・プロジェクトをまとめて変更
- **システムトレイ** — 常時トレイアイコン表示。最小化/閉じるでトレイに格納、多重起動防止
- **API サーバー** — Flask ベースの REST API。設定画面で有効化、外部ツールから HTTP 経由で操作可能
- **データ永続化** — SQLite (`data/tracker.db`)


## 起動方法

```bash
kousu-kanri-gui.exe
```

### API で使う

設定画面で「API サーバーを有効にする」をオンにしてアプリを再起動すると、`http://127.0.0.1:8321` で API が使えるようになる。

```bash
# ヘルスチェック
curl http://localhost:8321/api/health
# => {"status": "ok"}

# タスク一覧（今日）
curl http://localhost:8321/api/tasks
# 日付指定
curl http://localhost:8321/api/tasks?date=2026-03-08
# プロジェクト情報を省略
curl "http://localhost:8321/api/tasks?simple=1"

# タスク追加
curl -X POST http://localhost:8321/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"name": "コードレビュー", "start": "09:00", "end": "10:30"}'
# プロジェクト指定・日付指定
curl -X POST http://localhost:8321/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"name": "定例会", "start": "11:00", "end": "12:00", "project": "ミーティング", "date": "2026-03-08"}'

# プロジェクト一覧
curl http://localhost:8321/api/projects
# プロジェクト追加
curl -X POST http://localhost:8321/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "ミーティング", "color": "#4CAF50"}'

# 1日レポート（内訳付き）
curl "http://localhost:8321/api/report?date=2026-03-08&detail=1"
# 期間集計
curl "http://localhost:8321/api/reports?since=7d"
curl "http://localhost:8321/api/reports?from=2026-03-01&to=2026-03-08"
# 日別レポート
curl "http://localhost:8321/api/reports-by-day?since=30d&detail=1"
```

ブラウザで `http://localhost:8321/` を開くと、フォーム付きの HTML ページでタスクやレポートを閲覧できる。

> API 経由でタスクやプロジェクトを追加すると、GUI がリアルタイムで自動更新される（Qt シグナルによるイベント駆動）。

## セットアップ

### ビルド (exe)

[Nuitka](https://nuitka.net/) で Python なしで実行できる exe を生成できる。

```bash
# `dist/main.dist/` に exe と依存 DLL が生成される。
uv run python -m nuitka --standalone --enable-plugin=pyside6 --windows-console-mode=disable --windows-icon-from-ico=icon.ico --output-dir=dist --output-filename=kousu-kanri-gui.exe --assume-yes-for-downloads main.py
```

`dist/main.dist/` がそのまま配布フォルダになる。

> `v*` タグを push すると GitHub Actions で自動ビルド&リリースされる。

## アンインストール

アプリを削除する前に、設定画面の「Windows 起動時に自動起動する」のチェックを外して保存してください。

チェックを外さずに削除した場合は、以下のコマンドでレジストリを手動削除できます。

```bat
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v KousuKanri /f
```
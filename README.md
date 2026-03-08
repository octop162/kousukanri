# KousuKanri

タイムライン上でドラッグ&ドロップしながら作業時間を記録できるデスクトップアプリ。

## 機能

- **タイムライン** — 縦軸が時間。ドラッグで新規作成、ブロックの移動・リサイズ、ダブルクリックで隙間埋め
- **タイマー** — ワンクリックで計測開始。ブロックがリアルタイムに伸びる。開始時に自動で今日に切替
- **プロジェクト** — タスクをプロジェクトごとに色分け管理
- **ルーティン** — 定期タスクをプリセット登録してワンクリック追加
- **エクスポート** — テキスト形式でクリップボードにコピー
- **テーマ** — Dark / Light / Sky / Hacker / Monokai / Solarized
- **一括編集** — 複数タスクを選択して名前・プロジェクトをまとめて変更
- **CLI** — ターミナルからタスク追加・一覧表示・プロジェクト別レポート（`--yesterday` 対応）
- **システムトレイ** — 常時トレイアイコン表示。最小化/閉じるでトレイに格納、多重起動防止
- **データ永続化** — SQLite (`~/.tracker/tracker.db`)

## セットアップ

### 必要なもの

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)

### インストール

```bash
git clone <repository-url>
cd tracker
uv sync
```

### GUI で起動

```bash
uv run python main.py
```

### CLI で使う

```bash
# タスク追加
kousu-kanri.exe add "コードレビュー" 09:00 10:30
kousu-kanri.exe add "定例会" 11:00 12:00 --project ミーティング

# タスク一覧
kousu-kanri.exe list
kousu-kanri.exe list --date 2026-03-07

# プロジェクト管理
kousu-kanri.exe add-project "ミーティング" --color "#4CAF50"
kousu-kanri.exe list-projects

# レポート（プロジェクト別集計）
kousu-kanri.exe report
kousu-kanri.exe report --yesterday
kousu-kanri.exe report --date 2026-03-07

# 過去30日レポート
kousu-kanri.exe report-30d
kousu-kanri.exe report-30d --date 2026-03-01
```

## ビルド (exe)

[Nuitka](https://nuitka.net/) で Python なしで実行できる exe を生成できる。

```bash
# `dist/main.dist/` に exe と依存 DLL が生成される。
uv run python -m nuitka --standalone --enable-plugin=pyside6 --windows-console-mode=disable --windows-icon-from-ico=icon.ico --output-dir=dist --output-filename=kousu-kanri-gui.exe --assume-yes-for-downloads main.py
# `dist/cli.dist/` に生成される。exe を GUI の `dist/main.dist/` にコピーして一緒に配布できる。
uv run python -m nuitka --standalone --windows-icon-from-ico=icon.ico --output-dir=dist --output-filename=kousu-kanri.exe --assume-yes-for-downloads cli.py
# CLI の exe と DLL を GUI 側にコピーして1フォルダにまとめる
copy dist\cli.dist\kousu-kanri.exe dist\main.dist\
copy dist\cli.dist\*.dll dist\main.dist\
```

`dist/main.dist/` がそのまま配布フォルダになる。

> `v*` タグを push すると GitHub Actions で自動ビルド&リリースされる。

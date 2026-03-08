# KousuKanri

タイムライン上でドラッグ&ドロップしながら作業時間を記録できるデスクトップアプリ。

## 機能

- **タイムライン** — 縦軸が時間。ドラッグで新規作成、ブロックの移動・リサイズ、ダブルクリックで隙間埋め
- **タイマー** — ワンクリックで計測開始。ブロックがリアルタイムに伸びる
- **プロジェクト** — タスクをプロジェクトごとに色分け管理
- **ルーティン** — 定期タスクをプリセット登録してワンクリック追加
- **エクスポート** — テキスト形式でクリップボードにコピー
- **テーマ** — Dark / Light / Sky / Hacker / Monokai / Solarized
- **CLI** — ターミナルからタスク追加・一覧表示・プロジェクト別レポート
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
KousuKanri-cli.exe add "コードレビュー" 09:00 10:30
KousuKanri-cli.exe add "定例会" 11:00 12:00 --project ミーティング

# タスク一覧
KousuKanri-cli.exe list
KousuKanri-cli.exe list --date 2026-03-07

# プロジェクト管理
KousuKanri-cli.exe add-project "ミーティング" --color "#4CAF50"
KousuKanri-cli.exe list-projects

# レポート（プロジェクト別集計）
KousuKanri-cli.exe report
KousuKanri-cli.exe report --date 2026-03-07

# 過去30日レポート
KousuKanri-cli.exe report-30d
KousuKanri-cli.exe report-30d --date 2026-03-01
```

## ビルド (exe)

[Nuitka](https://nuitka.net/) で Python なしで実行できる exe を生成できる。

### GUI

```bash
uv run python -m nuitka --standalone --enable-plugin=pyside6 --windows-console-mode=disable --windows-icon-from-ico=icon.ico --output-dir=dist --output-filename=KousuKanri.exe --assume-yes-for-downloads main.py
```

`dist/main.dist/` に exe と依存 DLL が生成される。

### CLI

```bash
uv run python -m nuitka --standalone --windows-icon-from-ico=icon.ico --output-dir=dist --output-filename=KousuKanri-cli.exe --assume-yes-for-downloads cli.py
```

`dist/cli.dist/` に生成される。exe を GUI の `dist/main.dist/` にコピーして一緒に配布できる。

> `v*` タグを push すると GitHub Actions で自動ビルド&リリースされる。

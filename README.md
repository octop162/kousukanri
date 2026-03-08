# KousuKanri

タイムライン上でドラッグ&ドロップしながら作業時間を記録できるデスクトップアプリ。

## 機能

- **タイムライン** — 縦軸が時間。ドラッグで新規作成、ブロックの移動・リサイズ、ダブルクリックで隙間埋め
- **タイマー** — ワンクリックで計測開始。ブロックがリアルタイムに伸びる
- **プロジェクト** — タスクをプロジェクトごとに色分け管理
- **ルーティン** — 定期タスクをプリセット登録してワンクリック追加
- **エクスポート** — テキスト形式でクリップボードにコピー
- **テーマ** — Dark / Light / Sky / Hacker / Monokai / Solarized
- **CLI** — ターミナルからタスク追加・一覧表示
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
uv run python cli.py add "コードレビュー" 09:00 10:30
uv run python cli.py add "定例会" 11:00 12:00 --project ミーティング

# タスク一覧
uv run python cli.py list
uv run python cli.py list --date 2026-03-07
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
uv run python -m nuitka --onefile --windows-icon-from-ico=icon.ico --output-dir=dist --output-filename=KousuKanri-cli.exe --assume-yes-for-downloads cli.py
```

`dist/KousuKanri-cli.exe` が生成される。GUI の `dist/main.dist/` に入れて一緒に配布できる。

> `v*` タグを push すると GitHub Actions で自動ビルド&リリースされる。

# KousuKanri

工数（時間）管理ツール。PySide6 GUI + Flask API + React SPA の構成。

## 技術スタック
- Python + PySide6 (uv で管理)
- SQLite (WAL モード、`~/.tracker/tracker.db`)
- Flask (API サーバー、daemon スレッドで動作)
- React + TypeScript + Tailwind CSS + DaisyUI (Web UI、Vite でビルド → `static/` に出力)

## プロジェクト構成

```
tracker/
├── main.py                    # GUI エントリーポイント
├── api_server.py              # Flask API サーバー (daemon スレッド、設定で有効化、SPA 配信)
├── static/                    # React SPA ビルド成果物 (web/ から生成、gitignore)
├── web/                       # React フロントエンド (Vite + Tailwind + React Router)
│   ├── public/
│   │   ├── openapi.yaml       # OpenAPI 3.0 スペック (API の Single Source of Truth)
│   │   └── redoc.standalone.js
│   └── src/
│       ├── api.ts             # API クライアント + 型定義
│       ├── App.tsx            # ルーティング定義
│       ├── utils.ts           # fmtTime, today, thirtyDaysAgo
│       ├── components/        # Layout, ReportList, DateForm, DateRangeForm
│       └── pages/             # TasksPage, ProjectsPage, ReportDailyPage, ReportTasksPage
├── models/
│   ├── task.py                # Task dataclass (id, name, start_time, end_time, color, project_id)
│   ├── project.py             # Project dataclass (id, name, color, archived)
│   ├── routine.py             # Routine dataclass (定期タスクプリセット)
│   └── database.py            # SQLite DAL (WAL, CRUD, マイグレーション, check_same_thread対応)
├── views/
│   ├── main_window.py         # QMainWindow + QSplitter + システムトレイ + 多重起動防止 (1200x1000)
│   ├── timeline_view.py       # QGraphicsView (起動時 8:00 付近にスクロール)
│   ├── timeline_scene.py      # QGraphicsScene (D&D 新規作成・重複制御・ダブルクリック)
│   ├── task_block_item.py     # QGraphicsRectItem (移動・リサイズ・右クリック)
│   ├── time_ruler_item.py     # 左側に時刻ラベル + 横グリッド線 (1h/15min/5min の3段階)
│   ├── task_list_view.py      # タスクリスト (追加フォーム + テーブル、複数選択・一括編集)
│   ├── task_edit_dialog.py    # タスク編集ダイアログ (単体編集 + 一括編集)
│   ├── project_list_view.py   # プロジェクト管理 (CRUD + 色変更 + アーカイブ)
│   ├── timer_widget.py        # タイマーバー (タスク名・プロジェクト・経過時間・▶/■ボタン)
│   ├── date_nav_widget.py     # 日付ナビゲーション (◀/今日/▶ + カレンダーポップアップ)
│   ├── routine_view.py        # 定期タスク管理 (登録フォーム + テーブル + ワンクリック追加)
│   └── settings_view.py       # 設定画面 (スナップ・Shiftスナップ・表示範囲・テーマ・通知・APIサーバー)
├── controllers/
│   └── task_controller.py     # View ↔ Model/DB の仲介 (日付別インメモリ dict、reload_current_date)
└── utils/
    ├── constants.py            # 定数・time_to_y / y_to_time 変換
    ├── report_helpers.py       # レポート集計・フォーマット関数 (api_server が利用)
    ├── settings.py             # 設定の読み書き (~/.tracker/ or exe隣/data/)
    └── theme.py                # テーマ定義・適用 (dark/light/sky/black_green/monokai/solarized)
```

## 設計方針

| 項目 | 方針 |
|------|------|
| 座標系 | 縦軸 = 時間 (上→下)、`time_to_y` / `y_to_time` で統一変換 |
| スナップ | 通常: 設定値で吸着、Shift 押下中: 別設定値で吸着 (`y_to_time` の `snap_minutes` 引数で切り替え)。ドラッグ中もリアルタイムで視覚スナップ |
| レーン | 1レーンのみ（1人の作業、並行タスクなし） |
| シグナル | Scene が `task_created` / `task_changed` / `task_deleted` を発火 → Controller が受信 |
| DB 書き込み | mouseRelease 時のみ (ドラッグ中は UI のみ更新)。タイマーは stop 時のみ書き込み |
| 日付管理 | Controller が日付別インメモリ dict でキャッシュ、日付切替時に DB から遅延ロード |
| スレッド安全 | Flask は daemon スレッドで動作、SQLite WAL で GUI スレッドと並行アクセス |

## ブロック操作仕様

### 新規作成: 空き領域ドラッグ
- 空き領域を左ボタンでドラッグ → 仮ブロック表示 → リリースで確定
- ドラッグ中からスナップ後の位置にリアルタイムで仮ブロックが吸着
- Shift/Alt を押しながらドラッグすると対応するスナップ間隔で吸着
- 既存ブロックと重なる場合: 開始/終了を既存ブロックの境界にスナップ
- 開始も終了も塞がっている場合は作成しない

### 新規作成: 隙間ダブルクリック
- 空き領域をダブルクリック → 前後のブロック境界（または1日の開始/終了）いっぱいまで埋めるタスクを即座に作成

### 移動: ブロック中央ドラッグ
- ブロックの中央部分をドラッグ → 上下に移動（長さ保持）
- ドラッグ中からスナップ後の位置にリアルタイムで吸着
- Shift/Alt を押しながらドラッグすると対応するスナップ間隔で吸着
- 移動先に重なるブロックがある場合: 直後 or 直前の空きスロットにジャンプ（近い方優先）
- どちらにも収まらなければ元の位置に戻る

### リサイズ: ブロック端ドラッグ
- 上端/下端 8px 以内でカーソルが `SizeVerCursor` に変化
- ドラッグで開始/終了時刻を変更
- ドラッグ中からスナップ後の位置にリアルタイムで吸着
- Shift/Alt を押しながらドラッグすると対応するスナップ間隔で吸着
- **ドラッグしている端のみスナップ**（固定側の端は元の時刻を維持）
- 既存ブロックと重なる場合: 重なる側の端を既存ブロックの境界にスナップ

### 右クリックメニュー
- Rename: タスク名を変更 / Change Color: 色を変更 / Delete: ブロックを削除

## システムトレイ・通知
- トレイアイコン常時表示（起動直後から、終了時のみ非表示）
- 最小化・バツボタンでトレイに格納、ダブルクリックで復帰、右クリックで表示/終了
- 未計測時の通知: 5分間隔チェック、設定で ON/OFF 可
- 多重起動防止: QLocalServer/Socket により既存ウィンドウを前面に復帰

## タイマー
- タスク名・プロジェクト・経過時間・▶/■ボタン
- タイマー開始時に表示日が今日でなければ自動で今日に切り替え
- タイマー実行中の日付移動: タイマーは停止せず、表示日≠タスク日なら更新スキップ
- 補完候補は過去30日のタスク名に限定

## API サーバー (Flask)

デフォルト: `http://127.0.0.1:8321`。設定で有効化・ポート変更可。

### JSON API エンドポイント

| Method | Path | 説明 |
|--------|------|------|
| GET | `/api/health` | ヘルスチェック |
| GET | `/api/tasks?date=YYYY-MM-DD&simple=1` | タスク一覧 (デフォルト: 今日) |
| POST | `/api/tasks` | タスク追加 (`{name, start, end, date?, project?}`) |
| GET | `/api/projects` | プロジェクト一覧 (archived フィールド含む) |
| POST | `/api/projects` | プロジェクト追加 (`{name, color?}`) |
| PATCH | `/api/projects/<id>/archive` | プロジェクトアーカイブ/解除 (`{archived}`) |
| GET | `/api/report/daily?from=...&to=...` | 日別×プロジェクト別工数レポート |
| GET | `/api/report/tasks?from=...&to=...` | 期間全体×タスク別工数レポート |
| GET | `/api/docs` | ReDoc API ドキュメント |

### SPA ルーティング

| Path | 説明 |
|------|------|
| `/` | → `/tasks` にリダイレクト |
| `/tasks?date=...` | タスク一覧 |
| `/projects` | プロジェクト一覧 (アーカイブ管理) |
| `/report/daily?from=...&to=...` | 日別レポート |
| `/report/tasks?from=...&to=...` | タスク別レポート |

### GUI リアルタイム同期
- API POST → `ApiNotifier.data_changed` シグナル → Qt QueuedConnection でメインスレッドへ
- イベント駆動、ポーリングなし

## 起動・ビルド

```bash
# 開発
uv run python main.py

# Web UI 開発 (ホットリロード)
uv run python main.py          # API サーバーを有効化
cd web && npm run dev           # Vite dev server (/api は :8321 にプロキシ)

# Web UI ビルド
cd web && npm run build         # → ../static/ に出力
```

```powershell
# ローカルビルド (Nuitka)
cd web && npm run build && cd ..
uv run python -m nuitka --standalone --enable-plugin=pyside6 `
  --windows-console-mode=disable --windows-icon-from-ico=icon.ico `
  --include-data-dir=static/=static/ --output-dir=dist `
  --output-filename=kousu-kanri-gui.exe --assume-yes-for-downloads main.py
# 成果物: dist/main.dist/kousu-kanri-gui.exe
```

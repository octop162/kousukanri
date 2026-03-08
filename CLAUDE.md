# KousuKanri

時間管理できるツール。

## 技術スタック
- Python + PySide6 (uv で管理)
- SQLite (Phase 2 - 動作確認済み)

## プロジェクト構成

```
tracker/
├── main.py                    # GUI エントリーポイント
├── cli.py                     # CLI エントリーポイント (add/list/add-project/list-projects)
├── models/
│   ├── task.py                # Task dataclass (id, name, start_time, end_time, color, project_id)
│   ├── project.py             # Project dataclass (id, name, color)
│   ├── routine.py             # Routine dataclass (定期タスクプリセット)
│   └── database.py            # SQLite DAL (WAL, CRUD, ~/.tracker/tracker.db)
├── views/
│   ├── main_window.py         # QMainWindow + QSplitter + システムトレイ (1200x1000)
│   ├── timeline_view.py       # QGraphicsView (起動時 8:00 付近にスクロール)
│   ├── timeline_scene.py      # QGraphicsScene (D&D 新規作成・重複制御・ダブルクリック)
│   ├── task_block_item.py     # QGraphicsRectItem (移動・リサイズ・右クリック)
│   ├── time_ruler_item.py     # 左側に時刻ラベル + 横グリッド線
│   ├── task_list_view.py     # タスクリスト (Phase 1.5)
│   ├── task_edit_dialog.py   # タスク編集ダイアログ
│   ├── project_list_view.py  # プロジェクト管理 (Phase 1.7)
│   ├── timer_widget.py       # タイマーバー (Phase 1.8)
│   ├── date_nav_widget.py    # 日付ナビゲーション (◀/今日/▶ + カレンダー)
│   ├── routine_view.py       # 定期タスク管理 (ルーティン登録・ワンクリック追加)
│   ├── export_view.py        # 出力タブ (テキストエクスポート・クリップボードコピー)
│   └── settings_view.py      # 設定画面 (スナップ・表示範囲・テーマ・通知)
├── controllers/
│   └── task_controller.py     # View ↔ Model/DB の仲介 (日付別インメモリ dict)
└── utils/
    ├── constants.py            # 定数・time_to_y / y_to_time 変換
    ├── settings.py             # 設定の読み書き (~/.tracker/ or exe隣/data/)
    └── theme.py                # テーマ定義・適用 (dark/light/sky/hacker/monokai/solarized)
```

## 設計方針

| 項目 | 方針 |
|------|------|
| 座標系 | 縦軸 = 時間 (上→下)、`time_to_y` / `y_to_time` で統一変換 |
| スナップ | 5分単位に吸着 (`y_to_time` 内で処理) |
| レーン | 1レーンのみ（1人の作業、並行タスクなし） |
| シグナル | Scene が `task_created` / `task_changed` / `task_deleted` を発火 → Controller が受信 |
| DB 書き込み | mouseRelease 時のみ (ドラッグ中は UI のみ更新) |

## ブロック操作仕様

### 新規作成: 空き領域ドラッグ
- 空き領域を左ボタンでドラッグ → 仮ブロック表示 → リリースで確定
- 既存ブロックと重なる場合: 開始/終了を既存ブロックの境界にスナップ
- 開始も終了も塞がっている場合は作成しない

### 新規作成: 隙間ダブルクリック
- 空き領域をダブルクリック → 前後のブロック境界（または1日の開始/終了）いっぱいまで埋めるタスクを即座に作成

### 移動: ブロック中央ドラッグ
- ブロックの中央部分をドラッグ → 上下に移動（長さ保持）
- 移動先に重なるブロックがある場合: 直後 or 直前の空きスロットにジャンプ（近い方優先）
- どちらにも収まらなければ元の位置に戻る

### リサイズ: ブロック端ドラッグ
- 上端/下端 8px 以内でカーソルが `SizeVerCursor` に変化
- ドラッグで開始/終了時刻を変更
- 既存ブロックと重なる場合: 重なる側の端を既存ブロックの境界にスナップ

### 右クリックメニュー
- Rename: タスク名を変更
- Change Color: 色を変更
- Delete: ブロックを削除

## 進捗

### Phase 1: D&D 付き UI（動作確認済み）
- [x] constants.py, task.py
- [x] time_ruler_item.py (縦向き、左側に時刻ラベル)
- [x] timeline_scene.py (ドラッグ新規作成 + ダブルクリック隙間埋め)
- [x] task_block_item.py (移動・リサイズ・右クリック・重複防止)
- [x] controller, view, window, main.py

### Phase 1.5: タスクリスト UI（動作確認済み）
- [x] task_list_view.py (追加フォーム + テーブル表示)
- [x] main_window.py を QSplitter 化 (左: タイムライン / 右: リスト)
- [x] controller にリストビュー連携追加 (双方向同期)
- [x] main.py に TaskListView 接続

### Phase 1.6: タブ付きサイドパネル + 設定画面（動作確認済み）
- [x] settings_view.py (ダミー設定フォーム)
- [x] main_window.py に QTabWidget 追加 (タスク / 設定)
- [x] main.py に SettingsView 接続

### Phase 1.7: プロジェクト管理（動作確認済み）
- [x] models/project.py (Project dataclass)
- [x] models/task.py に project_id 追加
- [x] views/project_list_view.py (CRUD + 色変更)
- [x] controllers/task_controller.py にプロジェクト管理追加
- [x] views/task_list_view.py にプロジェクト列・コンボボックス追加
- [x] views/main_window.py に「プロジェクト」タブ追加
- [x] main.py に ProjectListView 接続

### Phase 1.8: タイマー計測機能（動作確認済み）
- [x] views/timer_widget.py (タスク名・プロジェクト・経過時間・▶/■ボタン)
- [x] controllers/task_controller.py にタイマー管理追加 (QObject継承、QTimer)
- [x] views/timeline_scene.py の update_task_block を位置・サイズ更新対応に拡張
- [x] views/main_window.py に TimerWidget 追加 (タブ上部に配置)
- [x] main.py に TimerWidget 接続

### Phase 1.9: 日付ナビゲーション・設定・テーマ拡充（動作確認済み）
- [x] views/date_nav_widget.py (◀/今日/▶ ボタン + QCalendarWidget ポップアップ)
- [x] controllers/task_controller.py を日付別ストレージに変更 (_tasks_by_date)
- [x] 日付切り替え時の scene/list 再描画 (clear_task_blocks + set_reference_date)
- [x] タイマー実行中の日付移動対応（タイマーは停止せず、表示日≠タスク日なら更新スキップ）
- [x] タイムライン表示範囲を設定で変更可能 (デフォルト 7:00〜22:00)
- [x] テーマ追加: ライト(旧パステル)・スカイ・ハッカー・Monokai・Solarized Light/Dark
- [x] プロジェクトプルダウンに色付き■アイコン表示

### Phase 1.9.1: テーマ色のタイマーボタン対応（動作確認済み）
- [x] utils/theme.py に timer_start / timer_stop / timer_add 色キー追加
- [x] views/timer_widget.py がテーマ色でボタン背景を描画

### Phase 1.10: 定期タスク（ルーティン）機能（動作確認済み）
- [x] models/routine.py (Routine dataclass)
- [x] views/routine_view.py (登録フォーム + テーブル + ワンクリック追加)
- [x] controllers/task_controller.py に set_routine_view 追加
- [x] views/main_window.py に「定期」タブ追加
- [x] main.py に RoutineView 接続

### Phase 2: SQLite 永続化（動作確認済み）
- [x] models/database.py (WAL, CRUD, インデックス, ~/.tracker/tracker.db)
- [x] controllers/task_controller.py に DB 書き込み追加 (全 CRUD + ルーティン管理)
- [x] views/routine_view.py に routine_created/routine_deleted シグナル + set_routines 追加
- [x] main.py に Database 生成・結線・has_data によるサンプルデータ条件分岐
- [x] 日付切替時の遅延ロード (_reload_views_for_date で DB から取得)
- [x] タイマー: tick では DB 書き込みなし、stop 時のみ書き込み

### Phase 2.1: CLI ツール（動作確認済み）
- [x] cli.py (argparse ベース、add/list/add-project/list-projects サブコマンド)
- [x] add: タスク名・開始・終了時刻・プロジェクト指定で DB に直接追加
- [x] list: 日付指定でタスク一覧表示 (開始時刻順)
- [x] add-project: プロジェクト追加 (名前・色指定)
- [x] list-projects: プロジェクト一覧表示

### Phase 2.2: CI/CD・ビルド・配布（動作確認済み）
- [x] .github/workflows/build-release.yml (Nuitka standalone ビルド)
- [x] GUI + CLI を zip に同梱してリリース
- [x] icon.png / icon.ico (アプリアイコン)
- [x] Nuitka ビルド時は exe 隣の data/ にデータ配置 (__compiled__ 判定)

### Phase 2.3: システムトレイ・通知（動作確認済み）
- [x] 最小化・バツボタンでシステムトレイに格納
- [x] トレイダブルクリックで復帰、右クリックで表示/終了メニュー
- [x] 未計測時の通知 (5分間隔チェック、設定で ON/OFF 可)
- [x] 設定画面にテスト通知ボタン追加

## 起動方法
```
# GUI
uv run python main.py

# CLI
uv run python cli.py add <name> <start> <end> [--project <name>] [--date <YYYY-MM-DD>]
uv run python cli.py list [--date <YYYY-MM-DD>]
uv run python cli.py add-project <name> [--color <#HEX>]
uv run python cli.py list-projects
```

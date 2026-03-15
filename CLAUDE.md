# KousuKanri

時間管理できるツール。

## 技術スタック
- Python + PySide6 (uv で管理)
- SQLite (Phase 2 - 動作確認済み)
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
│   │   └── redoc.standalone.js # ReDoc (ローカル配信、CDN 不使用、MIT)
│   ├── src/
│   │   ├── api.ts             # API クライアント + 型定義
│   │   ├── App.tsx            # ルーティング定義
│   │   ├── utils.ts           # fmtTime, today, thirtyDaysAgo
│   │   ├── components/        # Layout, ReportList, DateForm, DateRangeForm
│   │   └── pages/             # TasksPage, ProjectsPage, ReportDailyPage, ReportTasksPage
│   └── vite.config.ts         # outDir: ../static, proxy: /api → :8321
├── models/
│   ├── task.py                # Task dataclass (id, name, start_time, end_time, color, project_id)
│   ├── project.py             # Project dataclass (id, name, color, archived)
│   ├── routine.py             # Routine dataclass (定期タスクプリセット)
│   └── database.py            # SQLite DAL (WAL, CRUD, マイグレーション, ~/.tracker/tracker.db, check_same_thread対応)
├── views/
│   ├── main_window.py         # QMainWindow + QSplitter + システムトレイ常時表示 + 多重起動防止 (1200x1000)
│   ├── timeline_view.py       # QGraphicsView (起動時 8:00 付近にスクロール)
│   ├── timeline_scene.py      # QGraphicsScene (D&D 新規作成・重複制御・ダブルクリック)
│   ├── task_block_item.py     # QGraphicsRectItem (移動・リサイズ・右クリック)
│   ├── time_ruler_item.py     # 左側に時刻ラベル + 横グリッド線
│   ├── task_list_view.py     # タスクリスト (Phase 1.5)
│   ├── task_edit_dialog.py   # タスク編集ダイアログ (単体編集 + 一括編集)
│   ├── project_list_view.py  # プロジェクト管理 (Phase 1.7)
│   ├── timer_widget.py       # タイマーバー (Phase 1.8)
│   ├── date_nav_widget.py    # 日付ナビゲーション (◀/今日/▶ + カレンダー)
│   ├── routine_view.py       # 定期タスク管理 (ルーティン登録・ワンクリック追加)
│   └── settings_view.py      # 設定画面 (スナップ・Shiftスナップ・表示範囲・テーマ・通知・APIサーバー)
├── controllers/
│   └── task_controller.py     # View ↔ Model/DB の仲介 (日付別インメモリ dict、reload_current_date)
└── utils/
    ├── constants.py            # 定数・time_to_y / y_to_time 変換
    ├── report_helpers.py       # レポート集計・フォーマット関数 (api_server が利用)
    ├── settings.py             # 設定の読み書き (~/.tracker/ or exe隣/data/、api_server_enabled/api_port)
    └── theme.py                # テーマ定義・適用 (dark/light/sky/black_green/monokai/solarized)
```

## 設計方針

| 項目 | 方針 |
|------|------|
| 座標系 | 縦軸 = 時間 (上→下)、`time_to_y` / `y_to_time` で統一変換 |
| スナップ | 通常: 設定値で吸着、Shift 押下中: 別設定値で吸着 (`y_to_time` の `snap_minutes` 引数で切り替え) |
| レーン | 1レーンのみ（1人の作業、並行タスクなし） |
| シグナル | Scene が `task_created` / `task_changed` / `task_deleted` を発火 → Controller が受信 |
| DB 書き込み | mouseRelease 時のみ (ドラッグ中は UI のみ更新) |

## ブロック操作仕様

### 新規作成: 空き領域ドラッグ
- 空き領域を左ボタンでドラッグ → 仮ブロック表示 → リリースで確定
- Shift を押しながらリリースすると Shift 時スナップ間隔でスナップ
- 既存ブロックと重なる場合: 開始/終了を既存ブロックの境界にスナップ
- 開始も終了も塞がっている場合は作成しない

### 新規作成: 隙間ダブルクリック
- 空き領域をダブルクリック → 前後のブロック境界（または1日の開始/終了）いっぱいまで埋めるタスクを即座に作成

### 移動: ブロック中央ドラッグ
- ブロックの中央部分をドラッグ → 上下に移動（長さ保持）
- Shift を押しながらリリースすると Shift 時スナップ間隔でスナップ
- 移動先に重なるブロックがある場合: 直後 or 直前の空きスロットにジャンプ（近い方優先）
- どちらにも収まらなければ元の位置に戻る

### リサイズ: ブロック端ドラッグ
- 上端/下端 8px 以内でカーソルが `SizeVerCursor` に変化
- ドラッグで開始/終了時刻を変更
- Shift を押しながらリリースすると Shift 時スナップ間隔でスナップ
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

### Phase 2.2: CI/CD・ビルド・配布（動作確認済み）
- [x] .github/workflows/build-release.yml (Nuitka standalone ビルド)
- [x] CI で Web UI ビルド (npm ci + npm run build) → static/ 同梱
- [x] GUI ビルド: standalone + PySide6 プラグイン + static/ 同梱
- [x] icon.png / icon.ico (アプリアイコン)
- [x] Nuitka ビルド時は exe 隣の data/ にデータ配置 (__compiled__ 判定)

### Phase 2.3: システムトレイ・通知（動作確認済み）
- [x] トレイアイコン常時表示（起動直後から表示、終了時のみ非表示）
- [x] 最小化・バツボタンでシステムトレイに格納
- [x] トレイダブルクリックで復帰、右クリックで表示/終了メニュー
- [x] 未計測時の通知 (5分間隔チェック、設定で ON/OFF 可)
- [x] 設定画面にテスト通知ボタン追加
- [x] QLocalServer/Socket による多重起動防止（既存ウィンドウを前面に復帰）

### Phase 2.4: 一括編集（動作確認済み）
- [x] タスクリストで複数選択 → 右クリック「一括編集」（名前・プロジェクトをまとめて変更）
- [x] タイマー開始時に表示日が今日でなければ自動で今日に切り替え

### Phase 2.5: レポート機能（Web に移行済み、GUI タブ削除）
- [x] utils/report_helpers.py にレポート集計・フォーマット関数を集約 (プロジェクト別・タスク別)
- [x] API: `/api/report/daily` (日別×プロジェクト), `/api/report/tasks` (期間×タスク)
- [x] 時間表示: HH:MM 形式に統一

### Phase 2.6: API サーバー（動作確認済み）
- [x] api_server.py (Flask ベース、daemon スレッド、CORS 対応)
- [x] ApiNotifier(QObject) で API→GUI リアルタイム同期 (data_changed シグナル)
- [x] controller に reload_current_date() 追加 (キャッシュクリア + 全View更新)
- [x] main.py に ApiServer 起動・停止の結線追加 (atexit + server_close で確実にポート解放)
- [x] settings_view.py に API サーバー有効化・ポート設定 UI
- [x] models/database.py に check_same_thread パラメータ対応
- [x] pyproject.toml に flask>=3.0 依存追加
- [x] タスクブロックのテキスト折り返し (TextWordWrap)
- [x] ウィンドウタイトル・トレイ・通知を「工数管理」に変更
- [x] タイマー補完候補を過去30日に限定 (get_recent_task_names クエリ)
- [x] GUI の出力・レポート・シンプル表示タブは Web 移行に伴い削除済み

### Phase 2.7: React SPA フロントエンド（動作確認済み）
- [x] web/ に React + TypeScript + Tailwind + React Router で SPA 構築
- [x] pages: タスク、プロジェクト、日別レポート、タスク別レポート（`/` は `/tasks` にリダイレクト）
- [x] api.ts に全 API クライアント + 型定義
- [x] vite.config.ts: 開発時 proxy /api → :8321、ビルド outDir: ../static
- [x] api_server.py を SPA 配信サーバーに変更 (Jinja2 → static_folder + send_from_directory)
- [x] templates/ 削除（不要になったため）
- [x] .gitignore に web/node_modules/, static/ を追加
- [x] 共通コンポーネント: DateForm (単一日付 + ◀▶), DateRangeForm (期間)
- [x] 出力部分はテーブルレイアウト（時間列の縦位置揃え）
- [x] ライト/ダーク テーマ切替 (ナビ右上トグル、localStorage 保存、OS設定に初回追従)
- [x] フォント: Noto Sans JP、ベースサイズ 125%

#### JSON API エンドポイント (デフォルト: http://127.0.0.1:8321)

| Method | Path | 説明 |
|--------|------|------|
| GET | `/api/health` | ヘルスチェック (`{"status": "ok"}`) |
| GET | `/api/tasks?date=YYYY-MM-DD&simple=1` | タスク一覧 (デフォルト: 今日) |
| POST | `/api/tasks` | タスク追加 (`{name, start, end, date?, project?}`) |
| GET | `/api/projects` | プロジェクト一覧 (archived フィールド含む) |
| POST | `/api/projects` | プロジェクト追加 (`{name, color?}`) |
| PATCH | `/api/projects/<id>/archive` | プロジェクトアーカイブ/解除 (`{archived}`) |
| GET | `/api/report/daily?from=...&to=...` | 日別×プロジェクト別工数レポート |
| GET | `/api/report/tasks?from=...&to=...` | 期間全体×タスク別工数レポート |

#### SPA ルーティング (http://127.0.0.1:8321)

| Path | 説明 |
|------|------|
| `/` | → `/tasks` にリダイレクト |
| `/tasks?date=...` | タスク一覧 |
| `/projects` | プロジェクト一覧 (アーカイブ管理) |
| `/report/daily?from=...&to=...` | 日別レポート |
| `/report/tasks?from=...&to=...` | タスク別レポート |

#### スレッド安全性
- Flask は daemon スレッドで動作 (werkzeug, threaded=True)
- 専用 Database インスタンス (`check_same_thread=False`)
- SQLite WAL モードにより GUI スレッドと安全に並行アクセス
- POST 成功後に `ApiNotifier.data_changed.emit()` → Qt QueuedConnection でメインスレッドへ

#### API ドキュメント
- OpenAPI 3.0 スペック: `web/public/openapi.yaml`
- ReDoc UI: http://127.0.0.1:8321/api/docs (API サーバー起動中にアクセス)

#### GUI リアルタイム同期
- API POST → `ApiNotifier.data_changed` シグナル (同一プロセス、スレッド間)
- イベント駆動、ポーリングなし

### Phase 2.8: API ドキュメント（動作確認済み）
- [x] web/public/openapi.yaml (OpenAPI 3.0 スペック、全エンドポイント定義)
- [x] api_server.py に `/api/docs` エンドポイント追加 (ReDoc、ローカル JS)

### Phase 2.9: Shift スナップ（動作確認済み）
- [x] Shift を押しながらドラッグ操作（新規作成・移動・リサイズ）すると Shift 時スナップ間隔でスナップ
- [x] `y_to_time` に `snap_minutes` 引数追加、通常/Shift で切り替え
- [x] 設定画面に「Shift 時スナップ間隔」追加 (デフォルト: 5 分)

## 起動方法
```
kousu-kanri-gui.exe
```

### 開発時
```
uv run python main.py
```

### Web UI 開発 (ホットリロード)
```
# 1. GUI 側を起動してAPIサーバーを有効化
uv run python main.py

# 2. Vite dev server を起動 (/api は :8321 にプロキシ)
cd web && npm run dev
```

### Web UI ビルド
```
cd web && npm run build   # → ../static/ に出力
```

### ローカルビルド (Nuitka)
```powershell
# 1. Web UI ビルド (static/ に出力)
cd web && npm run build && cd ..

# 2. GUI ビルド (standalone、PySide6 プラグイン有効、static/ 同梱)
$nuitkaArgs = @(
    "--standalone"
    "--enable-plugin=pyside6"
    "--windows-console-mode=disable"
    "--windows-icon-from-ico=icon.ico"
    "--include-data-dir=static/=static/"
    "--output-dir=dist"
    "--output-filename=kousu-kanri-gui.exe"
    "--assume-yes-for-downloads"
    "main.py"
)
uv run python -m nuitka @nuitkaArgs

# 成果物: dist/main.dist/kousu-kanri-gui.exe
```

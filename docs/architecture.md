# アーキテクチャ

## 全体構成

MVC パターンをベースに、PySide6 のシグナル/スロットで各層を疎結合に接続する。

```
┌─────────────┐     Signal      ┌─────────────────┐     読み書き     ┌──────────┐
│   Views     │ ──────────────→ │  Controller     │ ─────────────→ │  Models  │
│             │ ←────────────── │  (TaskController)│ ←───────────── │          │
│ - Timeline  │   メソッド呼出   │                 │                │ - Task   │
│ - TaskList  │                 │ インメモリ dict   │                │ - Project│
│ - Timer     │                 │ (将来: SQLite)   │                │          │
└─────────────┘                 └─────────────────┘                └──────────┘
```

## データフロー

### タイムライン → コントローラ (Signal)
- `task_created(Task)` — ドラッグ or ダブルクリックでブロック作成時
- `task_changed(Task)` — 移動・リサイズ・リネーム・色変更時
- `task_deleted(str)` — 右クリック削除時

### コントローラ → ビュー (メソッド呼出)
- `list_view.add_task()` / `update_task()` / `remove_task()`
- `scene.update_task_block()` / `add_task_block()`
- `timer_widget.force_stop()`

### タスクリスト → コントローラ (Signal)
- `task_edited(Task)` — 単体編集
- `tasks_bulk_edited(list[Task])` — 一括編集（複数タスクの名前・プロジェクトをまとめて変更）
- `task_delete_requested(str)` — 削除

### タイマー → コントローラ (Signal)
- `timer_started(name, project_id)` — ▶ 押下（表示日が今日でなければ自動切替）
- `timer_stopped()` — ■ 押下
- `timer_name_changed(name)` / `timer_project_changed(project_id)` — 計測中の編集

## 座標系

縦軸が時間を表す。上が0:00、下が24:00。

```
Y=0    ─── 0:00
       │
       │  PIXELS_PER_HOUR = 200px / 時間
       │
Y=1600 ─── 8:00  (起動時ここにスクロール)
       │
Y=4800 ─── 24:00
```

変換関数:
- `time_to_y(datetime) → float` — 時刻からY座標
- `y_to_time(float, reference_date) → datetime` — Y座標から時刻 (5分スナップ付き)

## ウィンドウレイアウト

```
QMainWindow (900x700)
└── QSplitter (水平)
    ├── 左 [500px]: TimelineView (QGraphicsView)
    │   └── TimelineScene (QGraphicsScene)
    │       ├── TimeRulerItem (左側の時刻ラベル + グリッド線)
    │       └── TaskBlockItem × N (タスクブロック)
    └── 右 [400px]: QWidget (QVBoxLayout)
        ├── TimerWidget (タイマーバー)
        │   [タスク名] [プロジェクト▼] [00:00:00] [▶/■]
        └── QTabWidget
            ├── Tab "タスク": TaskListView
            ├── Tab "プロジェクト": ProjectListView
            └── Tab "設定": SettingsView
```

## ファイル一覧と役割

| ファイル | 役割 |
|---------|------|
| `main.py` | エントリーポイント。各コンポーネントの生成と接続。QLocalServer で多重起動防止 |
| `models/task.py` | Task dataclass (id, name, start_time, end_time, color, project_id) |
| `models/project.py` | Project dataclass (id, name, color) |
| `controllers/task_controller.py` | QObject。Signal受信、インメモリdict管理、ビュー間同期、タイマー制御 |
| `views/main_window.py` | QMainWindow。QSplitter + システムトレイ常時表示 |
| `views/timeline_view.py` | QGraphicsView。起動時8:00付近にスクロール |
| `views/timeline_scene.py` | QGraphicsScene。ドラッグ新規作成、ダブルクリック隙間埋め、重複解決 |
| `views/task_block_item.py` | QGraphicsRectItem。移動・リサイズ・右クリックメニュー |
| `views/time_ruler_item.py` | 左側の時刻ラベルとグリッド線 |
| `views/task_list_view.py` | タスク一覧テーブル + 複数選択・一括編集 |
| `views/project_list_view.py` | プロジェクトCRUD画面 |
| `views/timer_widget.py` | タイマーバー |
| `views/settings_view.py` | 設定画面 (ダミー) |
| `utils/constants.py` | 定数、座標変換関数 |

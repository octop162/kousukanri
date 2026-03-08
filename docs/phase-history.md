# Phase 実装履歴

## Phase 1: D&D 付きタイムライン UI

最初に作った基盤。縦軸タイムライン上でタスクブロックをドラッグ操作する。

### 実装内容
- **constants.py** — 座標系定数 (`PIXELS_PER_HOUR=200`, 5分スナップ等) と `time_to_y` / `y_to_time` 変換関数
- **task.py** — Task dataclass (`id`, `name`, `start_time`, `end_time`, `color`)
- **time_ruler_item.py** — 左側に0:00〜24:00の時刻ラベルとグリッド線を描画
- **timeline_scene.py** — QGraphicsScene。ドラッグで新規ブロック作成、ダブルクリックで隙間埋め、重複解決ロジック
- **task_block_item.py** — QGraphicsRectItem。中央ドラッグで移動、端ドラッグでリサイズ、右クリックメニュー (Rename/Change Color/Delete)
- **timeline_view.py** — QGraphicsView。起動時に8:00付近にスクロール
- **task_controller.py** — Signal受信、インメモリ辞書でタスク管理
- **main_window.py** — QMainWindow (900x700)
- **main.py** — エントリーポイント、ダークパレット設定

### ブロック操作
- 空き領域ドラッグ → 仮ブロック表示 → リリースで確定
- 空き領域ダブルクリック → 隙間いっぱいにタスク作成
- ブロック中央ドラッグ → 移動 (重複時は近い空きスロットにジャンプ)
- ブロック端ドラッグ → リサイズ (重複時は境界にスナップ)

---

## Phase 1.5: タスクリスト UI

右側にタスクリストを追加。タイムラインと双方向同期。

### 実装内容
- **task_list_view.py** — 上部に追加フォーム (タスク名入力 + 追加ボタン)、下部にテーブル表示 (タスク名/開始/終了/所要時間)
- **main_window.py** — QSplitter化 (左: タイムライン 500px / 右: リスト 400px)
- **task_controller.py** — `set_list_view()` で双方向同期を接続

### 同期の仕組み
- タイムライン操作 → Controller → `list_view.add_task()` / `update_task()` / `remove_task()`
- リスト追加フォーム → `task_add_requested` Signal → Controller → 重複解決 → タイムラインに追加

---

## Phase 1.6: タブ付きサイドパネル + 設定画面

右側をタブ化し、将来の機能拡張に備えた。

### 実装内容
- **settings_view.py** — ダミーの設定フォーム (将来の設定項目のプレースホルダー)
- **main_window.py** — 右側を QTabWidget に変更 (「タスク」「設定」タブ)

---

## Phase 1.7: プロジェクト管理

プロジェクト機能を追加。タスクにプロジェクトを紐付けて色分け。

### 実装内容
- **project.py** — Project dataclass (`id`, `name`, `color`)
- **task.py** — `project_id` フィールド追加
- **project_list_view.py** — プロジェクトCRUD (作成/リネーム/色変更/削除)
- **task_controller.py** — プロジェクト管理の Signal ハンドラ追加。プロジェクト色変更時に所属タスクの色を一括更新。プロジェクト削除時はタスクの `project_id` を None にして色は維持。
- **task_list_view.py** — プロジェクト列追加、追加フォームにプロジェクト選択コンボボックス、テーブルのプロジェクト列クリックで変更メニュー
- **task_block_item.py** — 右クリックメニューに「Change Project」サブメニュー追加
- **main_window.py** — 「プロジェクト」タブ追加

### プロジェクト → タスクの連携
- タスク作成時にプロジェクトを選択 → プロジェクトの色がブロックに反映
- プロジェクトの色変更 → 所属する全タスクの色が自動更新
- プロジェクト削除 → タスクの色はそのまま、project_id だけ None に

---

## Phase 1.8: タイマー計測機能

▶/■ ボタンでリアルタイム計測。ブロックが伸びていく。

### 実装内容
- **timer_widget.py** (新規) — 横並びレイアウト: タスク名入力 / プロジェクト選択 / 経過時間表示 / ▶■トグルボタン
- **task_controller.py** — QObject 継承に変更。`_running_task_id` と `_tick_timer` (1秒間隔 QTimer) でタイマー管理。計測中タスク削除のガード追加。
- **timeline_scene.py** — `update_task_block()` を拡張: 色だけでなく位置・サイズも更新 (ブロックがリアルタイムに伸びる)
- **main_window.py** — 右パネルを QWidget(QVBoxLayout) に変更: タイマーバー + タブ
- **main.py** — TimerWidget 生成と接続

### タイマーの動き
1. ▶ 押下 → `start_time=now` (5分スナップ) で Task 作成、タイムラインにブロック追加
2. 毎秒 → `end_time=now` に更新、ブロックが下に伸びる
3. ■ 押下 → `end_time` を5分スナップで確定、通常タスクになる
4. 計測中にタスク名・プロジェクト変更可能 (即座にブロック反映)
5. 計測中のブロックが右クリック削除された場合 → タイマーも強制停止 (`force_stop()`)

---

## Phase 2: SQLite 永続化

- `models/database.py` で WAL モードの SQLite 接続
- Controller に DB 読み書きを接続
- 日付切替時の遅延ロード
- タイマー: tick では DB 書き込みなし、stop 時のみ書き込み

---

## Phase 2.1: CLI ツール

ターミナルからタスクを操作する CLI。

- `cli.py` (argparse ベース)
- サブコマンド: `add`, `list`, `add-project`, `list-projects`, `report`, `report-30d`
- `report`: プロジェクト別レポート (`--date`, `--yesterday`)
- `report-30d`: 過去30日の日ごとレポート (`--date`)

---

## Phase 2.2: CI/CD・ビルド・配布

- `.github/workflows/build-release.yml` (Nuitka standalone ビルド)
- GUI (`kousu-kanri-gui.exe`) + CLI (`kousu-kanri.exe`) を zip に同梱してリリース
- `v*` タグ push で自動ビルド&リリース

---

## Phase 2.3: システムトレイ・通知・多重起動防止

- トレイアイコン常時表示（起動直後から表示、終了時のみ非表示）
- 最小化・バツボタンでトレイに格納、ダブルクリックで復帰
- 未計測時の通知 (5分間隔、設定で ON/OFF 可)
- QLocalServer/Socket による多重起動防止（2つ目の起動で既存ウィンドウを前面に復帰）

---

## Phase 2.4: 一括編集・タイマー改善

- タスクリストで Ctrl/Shift クリックによる複数選択
- 右クリック「一括編集」で名前・プロジェクトをまとめて変更（変更しないフィールドは元のまま）
- タイマー開始時に表示日が今日でなければ自動で今日に切り替え

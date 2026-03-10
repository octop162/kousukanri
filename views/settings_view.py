from PySide6.QtWidgets import (
    QWidget, QFormLayout, QSpinBox, QLabel, QPushButton, QMessageBox, QComboBox,
    QCheckBox, QHBoxLayout,
)
from PySide6.QtCore import Signal

from utils.settings import load_settings, save_settings
from utils.startup import is_startup_enabled, set_startup


class SettingsView(QWidget):
    settings_changed = Signal(dict)  # emitted with full settings dict

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load()

    def _init_ui(self):
        layout = QFormLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        header = QLabel("設定")
        header.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 8px;")
        layout.addRow(header)

        self._snap_spin = QSpinBox()
        self._snap_spin.setRange(1, 60)
        self._snap_spin.setSuffix(" 分")
        layout.addRow("スナップ間隔:", self._snap_spin)

        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(1, 480)
        self._duration_spin.setSuffix(" 分")
        layout.addRow("デフォルトタスク時間:", self._duration_spin)

        self._start_hour_spin = QSpinBox()
        self._start_hour_spin.setRange(0, 23)
        self._start_hour_spin.setSuffix(" 時")
        layout.addRow("タイムライン開始:", self._start_hour_spin)

        self._end_hour_spin = QSpinBox()
        self._end_hour_spin.setRange(1, 24)
        self._end_hour_spin.setSuffix(" 時")
        layout.addRow("タイムライン終了:", self._end_hour_spin)

        self._timeline_restart_label = QLabel("※ タイムライン表示範囲は再起動後に反映されます")
        self._timeline_restart_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addRow(self._timeline_restart_label)

        self._theme_combo = QComboBox()
        self._theme_combo.addItem("システムのテーマに合わせる", "system")
        self._theme_combo.addItem("ダーク", "dark")
        self._theme_combo.addItem("ライト", "light")
        self._theme_combo.addItem("空色", "sky")
        self._theme_combo.addItem("黒緑", "black_green")
        self._theme_combo.addItem("Monokai", "monokai")
        self._theme_combo.addItem("Solarized Light", "solarized_light")
        self._theme_combo.addItem("Solarized Dark", "solarized_dark")
        layout.addRow("テーマ:", self._theme_combo)

        self._restart_label = QLabel("※ テーマは再起動後に反映されます")
        self._restart_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addRow(self._restart_label)

        self._idle_notify_check = QCheckBox("未計測時に通知する")
        layout.addRow(self._idle_notify_check)

        self._startup_check = QCheckBox("Windows 起動時に自動起動する")
        layout.addRow(self._startup_check)

        self._api_server_check = QCheckBox("API サーバーを有効にする")
        layout.addRow(self._api_server_check)

        self._api_port_spin = QSpinBox()
        self._api_port_spin.setRange(1024, 65535)
        layout.addRow("API ポート:", self._api_port_spin)

        self._api_restart_label = QLabel("※ API サーバー設定は次回起動時に反映されます")
        self._api_restart_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addRow(self._api_restart_label)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._on_save)
        layout.addRow(save_btn)

    def _load(self):
        s = load_settings()
        self._snap_spin.setValue(s["snap_minutes"])
        self._duration_spin.setValue(s["default_duration_minutes"])
        self._start_hour_spin.setValue(s.get("timeline_start_hour", 0))
        self._end_hour_spin.setValue(s.get("timeline_end_hour", 24))
        theme = s.get("theme", "dark")
        for i in range(self._theme_combo.count()):
            if self._theme_combo.itemData(i) == theme:
                self._theme_combo.setCurrentIndex(i)
                break
        self._idle_notify_check.setChecked(s.get("idle_notify", True))
        self._api_server_check.setChecked(s.get("api_server_enabled", False))
        self._api_port_spin.setValue(s.get("api_port", 8321))
        self._startup_check.setChecked(is_startup_enabled())


    def _on_save(self):
        s = {
            "snap_minutes": self._snap_spin.value(),
            "default_duration_minutes": self._duration_spin.value(),
            "timeline_start_hour": self._start_hour_spin.value(),
            "timeline_end_hour": self._end_hour_spin.value(),
            "theme": self._theme_combo.currentData(),
            "idle_notify": self._idle_notify_check.isChecked(),
            "api_server_enabled": self._api_server_check.isChecked(),
            "api_port": self._api_port_spin.value(),
        }
        save_settings(s)
        set_startup(self._startup_check.isChecked())
        self.settings_changed.emit(s)
        QMessageBox.information(self, "設定", "保存しました。")

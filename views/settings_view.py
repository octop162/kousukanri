from PySide6.QtWidgets import QWidget, QFormLayout, QSpinBox, QComboBox, QLabel


class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QFormLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        header = QLabel("設定（ダミー）")
        header.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 8px;")
        layout.addRow(header)

        self.snap_interval = QSpinBox()
        self.snap_interval.setRange(1, 60)
        self.snap_interval.setValue(5)
        self.snap_interval.setSuffix(" 分")
        layout.addRow("スナップ間隔:", self.snap_interval)

        self.default_duration = QSpinBox()
        self.default_duration.setRange(5, 480)
        self.default_duration.setValue(30)
        self.default_duration.setSuffix(" 分")
        layout.addRow("デフォルトタスク時間:", self.default_duration)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        layout.addRow("テーマ:", self.theme_combo)

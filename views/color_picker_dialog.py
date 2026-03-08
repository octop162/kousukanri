from PySide6.QtWidgets import (
    QDialog, QGridLayout, QPushButton, QVBoxLayout, QLabel,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

# 36 colors: muted/pastel tones readable with both black and white text
PRESET_COLORS = [
    # Row 1: Reds / Pinks
    "#E57373", "#F06292", "#BA68C8", "#9575CD", "#7986CB", "#64B5F6",
    # Row 2: Blues / Cyans
    "#4FC3F7", "#4DD0E1", "#4DB6AC", "#81C784", "#AED581", "#DCE775",
    # Row 3: Yellows / Oranges
    "#FFF176", "#FFD54F", "#FFB74D", "#FF8A65", "#A1887F", "#90A4AE",
    # Row 4: Deeper pastels
    "#C75B5B", "#D4598A", "#9C56B0", "#7E57B2", "#5C6BC0", "#42A5F5",
    # Row 5: Deeper cool
    "#29B6F6", "#26C6DA", "#26A69A", "#66BB6A", "#9CCC65", "#C0CA33",
    # Row 6: Deeper warm / neutrals
    "#FFCA28", "#FFA726", "#FF7043", "#E05B5B", "#8D6E63", "#78909C",
]


class ColorPickerDialog(QDialog):
    """Grid-based color picker with preset colors."""

    def __init__(self, current_color: str = "#4A90D9", parent=None):
        super().__init__(parent)
        self.setWindowTitle("色を選択")
        self._selected_color = current_color

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        grid = QGridLayout()
        grid.setSpacing(4)

        for i, color in enumerate(PRESET_COLORS):
            row = i // 6
            col = i % 6
            btn = QPushButton()
            btn.setFixedSize(36, 36)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {color}; border: 2px solid transparent; "
                f"border-radius: 4px; }}"
                f"QPushButton:hover {{ border: 2px solid white; }}"
            )
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, c=color: self._pick(c))
            grid.addWidget(btn, row, col)

        layout.addLayout(grid)

        # Preview
        self._preview = QLabel()
        self._preview.setFixedHeight(28)
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_preview(current_color)
        layout.addWidget(self._preview)

    def _update_preview(self, color: str):
        self._preview.setStyleSheet(
            f"background-color: {color}; border-radius: 4px; font-weight: bold;"
        )
        self._preview.setText(color)

    def _pick(self, color: str):
        self._selected_color = color
        self.accept()

    def selected_color(self) -> str:
        return self._selected_color

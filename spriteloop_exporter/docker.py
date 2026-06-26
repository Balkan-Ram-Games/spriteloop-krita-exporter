import os

from krita import DockWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGroupBox, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from .extension import show_export_dialog


class SpriteLoopExporterDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SpriteLoop")

        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        logo_path = os.path.join(os.path.dirname(__file__), "spriteloop-logo.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        title = QLabel("SpriteLoop")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")

        export_button = QPushButton("Export Package")
        export_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        export_button.setMinimumHeight(34)
        export_button.clicked.connect(lambda: show_export_dialog(self))

        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()
        actions_layout.addWidget(export_button)
        actions_group.setLayout(actions_layout)

        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addWidget(actions_group)
        layout.addStretch(1)
        panel.setLayout(layout)
        self.setWidget(panel)

    def canvasChanged(self, canvas):
        pass

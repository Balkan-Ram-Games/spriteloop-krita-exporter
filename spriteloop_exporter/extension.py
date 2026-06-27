from krita import Extension, Krita
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QVBoxLayout,
)
import os

from .exporter import ExportOptions, SpriteLoopExportError, export_document


SETTINGS_GROUP = "spriteloop_exporter"
LAST_EXPORT_DIR_KEY = "last_export_dir"
EXPORT_GROUPS_AS_IMAGES_KEY = "export_groups_as_images"
VISIBLE_ONLY_KEY = "visible_only"


class SpriteLoopExporterExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction(
            "spriteloop_export_package",
            "Export SpriteLoop Package",
            "tools/scripts",
        )
        action.triggered.connect(self.export_package)

    def export_package(self):
        show_export_dialog()


def show_export_dialog(parent=None):
    document = Krita.instance().activeDocument()
    if document is None:
        QMessageBox.warning(parent, "SpriteLoop Exporter", "Open a Krita document before exporting.")
        return

    dialog = ExportOptionsDialog(parent)
    if dialog.exec_() != QDialog.Accepted:
        return
    values = dialog.values()

    app = Krita.instance()
    progress_dialog = QProgressDialog("Preparing export...", "Cancel", 0, 0, parent)
    progress_dialog.setWindowTitle("SpriteLoop Export")
    progress_dialog.setWindowModality(Qt.ApplicationModal)
    progress_dialog.setMinimumDuration(0)
    progress_dialog.show()
    QApplication.processEvents()

    def update_progress(current: int, total: int, node_name: str) -> None:
        progress_dialog.setMaximum(total)
        progress_dialog.setValue(current)
        progress_dialog.setLabelText("Exporting {} ({}/{})".format(node_name, current, total))
        QApplication.processEvents()
        if progress_dialog.wasCanceled():
            raise SpriteLoopExportError("Export canceled.")

    try:
        set_batch_mode(app, True)
        try:
            result = export_document(
                document,
                values["export_dir"],
                ExportOptions(
                    visible_only=values["visible_only"],
                    export_groups_as_images=values["export_groups_as_images"],
                ),
                update_progress,
            )
        finally:
            set_batch_mode(app, False)
            progress_dialog.close()
    except SpriteLoopExportError as exc:
        QMessageBox.critical(parent, "SpriteLoop Export Failed", str(exc))
        return
    except Exception as exc:
        QMessageBox.critical(parent, "SpriteLoop Export Failed", "Unexpected error: {}".format(exc))
        return

    QMessageBox.information(
        parent,
        "SpriteLoop Export Complete",
        "Exported {} part(s).\n\n{}".format(result.part_count, result.metadata_path),
    )


class ExportOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export SpriteLoop Package")
        self.setMinimumWidth(520)
        self.resize(560, 360)
        last_export_dir = read_plugin_setting(LAST_EXPORT_DIR_KEY, "")

        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        logo_path = os.path.join(os.path.dirname(__file__), "ui-logo.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        title = QLabel("SpriteLoop")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: 600;")

        self.export_dir = QLineEdit()
        self.export_dir.setReadOnly(True)
        self.export_dir.setText(last_export_dir)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.choose_export_dir)

        folder_row = QHBoxLayout()
        folder_row.addWidget(self.export_dir)
        folder_row.addWidget(browse_button)

        destination_group = QGroupBox("Destination")
        destination_form = QFormLayout()
        destination_form.addRow("Export folder", folder_row)
        destination_group.setLayout(destination_form)

        self.export_groups_as_images = QCheckBox("Export groups as images")
        self.export_groups_as_images.setChecked(
            read_bool_plugin_setting(EXPORT_GROUPS_AS_IMAGES_KEY, True)
        )

        self.visible_only = QCheckBox("Export visible layers only")
        self.visible_only.setChecked(read_bool_plugin_setting(VISIBLE_ONLY_KEY, True))

        content_group = QGroupBox("Export Content")
        content_layout = QVBoxLayout()
        content_layout.addWidget(self.export_groups_as_images)
        content_layout.addWidget(self.visible_only)
        content_group.setLayout(content_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addWidget(destination_group)
        layout.addWidget(content_group)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def choose_export_dir(self):
        start_dir = self.export_dir.text().strip() or read_plugin_setting(LAST_EXPORT_DIR_KEY, "")
        if start_dir and not os.path.isdir(start_dir):
            start_dir = ""
        export_dir = QFileDialog.getExistingDirectory(
            self,
            "Export SpriteLoop Package",
            start_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if export_dir:
            self.export_dir.setText(export_dir)

    def accept(self):
        if not self.export_dir.text().strip():
            QMessageBox.warning(self, "SpriteLoop Exporter", "Choose an export folder.")
            return
        write_plugin_setting(LAST_EXPORT_DIR_KEY, self.export_dir.text().strip())
        write_plugin_setting(
            EXPORT_GROUPS_AS_IMAGES_KEY,
            bool_to_setting(self.export_groups_as_images.isChecked()),
        )
        write_plugin_setting(VISIBLE_ONLY_KEY, bool_to_setting(self.visible_only.isChecked()))
        super().accept()

    def values(self):
        return {
            "export_dir": self.export_dir.text().strip(),
            "export_groups_as_images": self.export_groups_as_images.isChecked(),
            "visible_only": self.visible_only.isChecked(),
        }


def set_batch_mode(app, enabled: bool) -> None:
    setter = getattr(app, "setBatchmode", None)
    if callable(setter):
        setter(enabled)


def read_plugin_setting(key: str, default: str) -> str:
    reader = getattr(Krita.instance(), "readSetting", None)
    if not callable(reader):
        return default
    value = reader(SETTINGS_GROUP, key, default)
    return value if value else default


def write_plugin_setting(key: str, value: str) -> None:
    writer = getattr(Krita.instance(), "writeSetting", None)
    if callable(writer):
        writer(SETTINGS_GROUP, key, value)


def read_bool_plugin_setting(key: str, default: bool) -> bool:
    value = read_plugin_setting(key, bool_to_setting(default)).strip().lower()
    return value in ("1", "true", "yes", "on")


def bool_to_setting(value: bool) -> str:
    return "true" if value else "false"

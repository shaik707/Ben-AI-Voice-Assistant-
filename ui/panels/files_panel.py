# ui/panels/files_panel.py — File Manager Panel

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QLineEdit, QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt


class FilesPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.current_path = os.path.expanduser("~")
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = QLabel("📁 File Manager")
        header.setStyleSheet("color: #00c8ff; font-size: 18px; font-weight: bold; padding: 4px;")
        layout.addWidget(header)

        # Path bar
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit(self.current_path)
        self.path_input.setMinimumHeight(36)
        self.path_input.returnPressed.connect(self._navigate_path)
        path_layout.addWidget(self.path_input, 1)

        up_btn = QPushButton("⬆️ Up")
        up_btn.setMinimumHeight(36)
        up_btn.clicked.connect(self._go_up)
        path_layout.addWidget(up_btn)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(36, 36)
        refresh_btn.clicked.connect(self._refresh)
        path_layout.addWidget(refresh_btn)

        layout.addLayout(path_layout)

        # File list
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget { background-color: #0d1117; border: 1px solid #1a2332; border-radius: 8px; }
            QListWidget::item { padding: 8px; border-radius: 4px; margin: 1px; }
            QListWidget::item:hover { background-color: rgba(0, 200, 255, 0.08); }
            QListWidget::item:selected { background-color: rgba(0, 200, 255, 0.15); }
        """)
        self.file_list.itemDoubleClicked.connect(self._open_item)
        layout.addWidget(self.file_list, 1)

        # Actions
        actions_layout = QHBoxLayout()
        for text, callback in [
            ("📄 New File", self._new_file),
            ("📂 New Folder", self._new_folder),
            ("🗑️ Delete", self._delete_item),
            ("📂 Open in System", self._open_in_system),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            actions_layout.addWidget(btn)
        layout.addLayout(actions_layout)

        # Info
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #8b949e; font-size: 11px; padding: 4px;")
        layout.addWidget(self.info_label)

    def _refresh(self):
        self.file_list.clear()
        try:
            items = sorted(os.listdir(self.current_path))
            dirs = [i for i in items if os.path.isdir(os.path.join(self.current_path, i))]
            files = [i for i in items if os.path.isfile(os.path.join(self.current_path, i))]

            for d in dirs:
                if not d.startswith('.'):
                    item = QListWidgetItem(f"📂 {d}")
                    item.setData(Qt.ItemDataRole.UserRole, os.path.join(self.current_path, d))
                    self.file_list.addItem(item)

            for f in files:
                if not f.startswith('.'):
                    size = os.path.getsize(os.path.join(self.current_path, f))
                    size_str = self._format_size(size)
                    icon = self._get_icon(f)
                    item = QListWidgetItem(f"{icon} {f}  ({size_str})")
                    item.setData(Qt.ItemDataRole.UserRole, os.path.join(self.current_path, f))
                    self.file_list.addItem(item)

            self.info_label.setText(f"{len(dirs)} folders, {len(files)} files")
            self.path_input.setText(self.current_path)
        except PermissionError:
            self.info_label.setText("Permission denied")
        except Exception as e:
            self.info_label.setText(str(e))

    def _open_item(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if os.path.isdir(path):
            self.current_path = path
            self._refresh()
        else:
            import subprocess, platform
            system = platform.system()
            if system == "Windows":
                os.startfile(path)
            elif system == "Darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])

    def _go_up(self):
        self.current_path = os.path.dirname(self.current_path)
        self._refresh()

    def _navigate_path(self):
        path = self.path_input.text().strip()
        if os.path.isdir(path):
            self.current_path = path
            self._refresh()

    def _new_file(self):
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "New File", "File name:")
        if ok and name:
            path = os.path.join(self.current_path, name)
            with open(path, 'w') as f:
                f.write("")
            self._refresh()

    def _new_folder(self):
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            os.makedirs(os.path.join(self.current_path, name), exist_ok=True)
            self._refresh()

    def _delete_item(self):
        item = self.file_list.currentItem()
        if item:
            path = item.data(Qt.ItemDataRole.UserRole)
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(self, "Delete",
                f"Delete '{os.path.basename(path)}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                import shutil
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self._refresh()

    def _open_in_system(self):
        import subprocess, platform
        system = platform.system()
        if system == "Windows":
            os.startfile(self.current_path)
        elif system == "Darwin":
            subprocess.run(["open", self.current_path])
        else:
            subprocess.run(["xdg-open", self.current_path])

    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _get_icon(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        icons = {
            '.py': '🐍', '.js': '📜', '.html': '🌐', '.css': '🎨',
            '.json': '📋', '.txt': '📄', '.md': '📝', '.pdf': '📕',
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
            '.mp3': '🎵', '.wav': '🎵', '.mp4': '🎬', '.avi': '🎬',
            '.zip': '📦', '.tar': '📦', '.gz': '📦',
        }
        return icons.get(ext, '📄')

    def cleanup(self):
        pass

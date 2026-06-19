# ui/panels/terminal_panel.py — Terminal Emulator Panel

import subprocess
import threading
import platform

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QTextCursor


class TerminalWorker(QObject):
    output_ready = pyqtSignal(str)
    error_ready = pyqtSignal(str)

    def run_command(self, command, cwd=None):
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=30, cwd=cwd
            )
            if result.stdout:
                self.output_ready.emit(result.stdout)
            if result.stderr:
                self.error_ready.emit(result.stderr)
            if not result.stdout and not result.stderr:
                self.output_ready.emit("(command executed - no output)\n")
        except subprocess.TimeoutExpired:
            self.error_ready.emit("Command timed out (30s limit)\n")
        except Exception as e:
            self.error_ready.emit(f"Error: {str(e)}\n")


class TerminalPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.cwd = None
        self.worker = TerminalWorker()
        self.worker.output_ready.connect(self._on_output)
        self.worker.error_ready.connect(self._on_error)
        self.history = []
        self.history_index = -1
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = QLabel("⌨️ Terminal")
        header.setStyleSheet("color: #00c8ff; font-size: 18px; font-weight: bold; padding: 4px;")
        layout.addWidget(header)

        # Terminal output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Menlo", 12) if platform.system() == "Darwin"
                           else QFont("Consolas", 11))
        self.output.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117;
                border: 1px solid #1a2332;
                border-radius: 8px;
                padding: 12px;
                color: #3fb950;
                font-size: 12px;
            }
        """)
        welcome = f"BENN AI Terminal — {platform.system()} {platform.release()}\nType commands below.\n\n"
        self.output.setPlainText(welcome)
        layout.addWidget(self.output, 1)

        # Input
        input_layout = QHBoxLayout()

        prompt = QLabel("$")
        prompt.setStyleSheet("color: #00c8ff; font-size: 16px; font-weight: bold; padding: 0 4px;")
        prompt.setFixedWidth(20)
        input_layout.addWidget(prompt)

        self.cmd_input = QLineEdit()
        self.cmd_input.setFont(QFont("Menlo", 12) if platform.system() == "Darwin"
                              else QFont("Consolas", 11))
        self.cmd_input.setPlaceholderText("Enter command...")
        self.cmd_input.setMinimumHeight(40)
        self.cmd_input.setStyleSheet("""
            QLineEdit {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e0e6f0;
                font-size: 12px;
            }
            QLineEdit:focus { border-color: #00c8ff; }
        """)
        self.cmd_input.returnPressed.connect(self._execute)
        input_layout.addWidget(self.cmd_input, 1)

        run_btn = QPushButton("▶")
        run_btn.setObjectName("primaryBtn")
        run_btn.setFixedSize(40, 40)
        run_btn.clicked.connect(self._execute)
        input_layout.addWidget(run_btn)

        clear_btn = QPushButton("🗑️")
        clear_btn.setFixedSize(40, 40)
        clear_btn.setToolTip("Clear terminal")
        clear_btn.clicked.connect(self._clear)
        input_layout.addWidget(clear_btn)

        layout.addLayout(input_layout)

    def _execute(self):
        command = self.cmd_input.text().strip()
        if not command:
            return

        self.history.append(command)
        self.history_index = len(self.history)

        # Display command
        self.output.append(f'<span style="color: #00c8ff;">$ {command}</span>')

        # Handle cd separately
        if command.startswith("cd "):
            import os
            path = command[3:].strip()
            try:
                expanded = os.path.expanduser(path)
                if os.path.isdir(expanded):
                    self.cwd = expanded
                    os.chdir(expanded)
                    self.output.append(f"Changed directory to: {expanded}\n")
                else:
                    self.output.append(f"Directory not found: {path}\n")
            except Exception as e:
                self.output.append(f"Error: {e}\n")
        else:
            # Run in thread
            def run():
                self.worker.run_command(command, cwd=self.cwd)
            threading.Thread(target=run, daemon=True).start()

        self.cmd_input.clear()

    def _on_output(self, text):
        self.output.append(f'<pre style="color: #e0e6f0; margin: 0;">{text}</pre>')
        self._scroll_bottom()

    def _on_error(self, text):
        self.output.append(f'<pre style="color: #f85149; margin: 0;">{text}</pre>')
        self._scroll_bottom()

    def _clear(self):
        self.output.clear()

    def _scroll_bottom(self):
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output.setTextCursor(cursor)

    def keyPressEvent(self, event):
        # Arrow keys for history navigation
        if event.key() == Qt.Key.Key_Up and self.history:
            self.history_index = max(0, self.history_index - 1)
            self.cmd_input.setText(self.history[self.history_index])
        elif event.key() == Qt.Key.Key_Down and self.history:
            self.history_index = min(len(self.history), self.history_index + 1)
            if self.history_index < len(self.history):
                self.cmd_input.setText(self.history[self.history_index])
            else:
                self.cmd_input.clear()
        else:
            super().keyPressEvent(event)

    def cleanup(self):
        pass

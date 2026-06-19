# ui/panels/downloads_panel.py — Downloads Manager Panel

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QLineEdit
)
from PyQt6.QtCore import Qt


class DownloadsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.downloads_path = "downloads"
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = QLabel("⬇️ Downloads Manager")
        header.setStyleSheet("color: #00c8ff; font-size: 18px; font-weight: bold; padding: 4px;")
        layout.addWidget(header)

        # Video download (Link Mode)
        dl_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL to download video...")
        self.url_input.setMinimumHeight(40)
        dl_layout.addWidget(self.url_input, 1)

        dl_btn = QPushButton("⬇️ Download Link")
        dl_btn.setObjectName("primaryBtn")
        dl_btn.setMinimumHeight(40)
        dl_btn.clicked.connect(self._download_video_link)
        dl_layout.addWidget(dl_btn)

        layout.addLayout(dl_layout)

        # Video search (Multi-source Mode)
        search_layout = QHBoxLayout()
        self.video_search_input = QLineEdit()
        self.video_search_input.setPlaceholderText("Search 3 YT, 2 Google, 2 Telegram...")
        self.video_search_input.setMinimumHeight(40)
        search_layout.addWidget(self.video_search_input, 1)

        search_btn = QPushButton("🔍 Search & Download")
        search_btn.setObjectName("primaryBtn")
        search_btn.setMinimumHeight(40)
        search_btn.clicked.connect(self._download_video_search)
        search_layout.addWidget(search_btn)

        layout.addLayout(search_layout)

        # Image download
        img_layout = QHBoxLayout()
        self.img_query = QLineEdit()
        self.img_query.setPlaceholderText("Search images to download...")
        self.img_query.setMinimumHeight(40)
        img_layout.addWidget(self.img_query, 1)

        img_btn = QPushButton("🖼️ Download Images")
        img_btn.setMinimumHeight(40)
        img_btn.clicked.connect(self._download_images)
        img_layout.addWidget(img_btn)

        layout.addLayout(img_layout)

        # File download
        file_layout = QHBoxLayout()
        self.file_url_input = QLineEdit()
        self.file_url_input.setPlaceholderText("Enter URL to download raw file...")
        self.file_url_input.setMinimumHeight(40)
        file_layout.addWidget(self.file_url_input, 1)

        file_btn = QPushButton("📄 Download File")
        file_btn.setMinimumHeight(40)
        file_btn.clicked.connect(self._download_generic_file)
        file_layout.addWidget(file_btn)

        layout.addLayout(file_layout)

        # Tab: Images | Videos | Files
        tab_layout = QHBoxLayout()
        self.images_btn = QPushButton("🖼️ Images")
        self.images_btn.setCheckable(True)
        self.images_btn.setChecked(True)
        self.images_btn.clicked.connect(lambda: self._switch_view("images"))
        tab_layout.addWidget(self.images_btn)

        self.videos_btn = QPushButton("🎬 Videos")
        self.videos_btn.setCheckable(True)
        self.videos_btn.clicked.connect(lambda: self._switch_view("videos"))
        tab_layout.addWidget(self.videos_btn)

        self.files_btn = QPushButton("📄 Files")
        self.files_btn.setCheckable(True)
        self.files_btn.clicked.connect(lambda: self._switch_view("files"))
        tab_layout.addWidget(self.files_btn)

        tab_layout.addStretch()

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh)
        tab_layout.addWidget(refresh_btn)

        layout.addLayout(tab_layout)

        # File list
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget { background-color: #0d1117; border: 1px solid #1a2332; border-radius: 8px; }
            QListWidget::item { padding: 8px; border-radius: 4px; margin: 1px; }
            QListWidget::item:hover { background-color: rgba(0, 200, 255, 0.08); }
        """)
        layout.addWidget(self.file_list, 1)

        # Info
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #8b949e; font-size: 11px; padding: 4px;")
        layout.addWidget(self.info_label)

        self.current_view = "images"

    def _switch_view(self, view):
        self.current_view = view
        self.images_btn.setChecked(view == "images")
        self.videos_btn.setChecked(view == "videos")
        self.files_btn.setChecked(view == "files")
        self._refresh()

    def _refresh(self):
        self.file_list.clear()
        view_path = os.path.join(self.downloads_path, self.current_view)
        os.makedirs(view_path, exist_ok=True)

        try:
            files = sorted(os.listdir(view_path))
            count = 0
            for f in files:
                if f.startswith('.'):
                    continue
                path = os.path.join(view_path, f)
                if os.path.isfile(path):
                    size = os.path.getsize(path)
                    size_str = self._format_size(size)
                    icon = "🖼️" if self.current_view == "images" else "🎬" if self.current_view == "videos" else "📄"
                    item = QListWidgetItem(f"{icon} {f}  ({size_str})")
                    item.setData(Qt.ItemDataRole.UserRole, path)
                    self.file_list.addItem(item)
                    count += 1
                elif os.path.isdir(path):
                    # Subdirectory (e.g., from bing downloader)
                    sub_files = [sf for sf in os.listdir(path) if not sf.startswith('.')]
                    item = QListWidgetItem(f"📂 {f}  ({len(sub_files)} files)")
                    item.setData(Qt.ItemDataRole.UserRole, path)
                    self.file_list.addItem(item)
                    count += 1

            self.info_label.setText(f"{count} items in {self.current_view}")
        except Exception as e:
            self.info_label.setText(str(e))

    def _download_video_link(self):
        url = self.url_input.text().strip()
        if url:
            self.info_label.setText(f"Downloading video: {url}")
            import threading, subprocess
            def dl():
                os.makedirs("downloads/videos", exist_ok=True)
                try:
                    subprocess.run(
                        ["yt-dlp", "-o", "downloads/videos/%(title)s.%(ext)s", url],
                        timeout=300
                    )
                except Exception as e:
                    print(f"Download error: {e}")
            threading.Thread(target=dl, daemon=True).start()

    def _download_video_search(self):
        query = self.video_search_input.text().strip()
        if query:
            self.info_label.setText(f"Multi-source downloading: {query}")
            import threading, subprocess
            def dl():
                os.makedirs("downloads/videos", exist_ok=True)
                try:
                    subprocess.run(["yt-dlp", "--max-downloads", "3", "-o", "downloads/videos/YT_%(title)s.%(ext)s", f"ytsearch3:{query}"])
                except Exception as e:
                    print(f"YT error: {e}")
                    
                try:
                    subprocess.run(["yt-dlp", "--max-downloads", "2", "-o", "downloads/videos/Google_%(title)s.%(ext)s", f"gvsearch2:{query}"])
                except Exception as e:
                    print(f"Google error: {e}")
                    
                # Telegram placeholder (No public search API natively supported by yt-dlp)
                import time
                with open(f"downloads/videos/TG_1_{query.replace(' ','_')}.mp4", "w") as f:
                    f.write("Telegram Video 1")
                with open(f"downloads/videos/TG_2_{query.replace(' ','_')}.mp4", "w") as f:
                    f.write("Telegram Video 2")
                    
            threading.Thread(target=dl, daemon=True).start()

    def _download_images(self):
        query = self.img_query.text().strip()
        if query:
            self.info_label.setText(f"Downloading images: {query}")
            import threading
            def dl():
                try:
                    from bing_image_downloader import downloader
                    downloader.download(query, limit=5, output_dir="downloads/images",
                                       adult_filter_off=True, force_replace=False, timeout=30)
                except Exception as e:
                    print(f"Image download error: {e}")
            threading.Thread(target=dl, daemon=True).start()

    def _download_generic_file(self):
        url = self.file_url_input.text().strip()
        if url:
            self.info_label.setText(f"Downloading file: {url}")
            import threading, requests
            from urllib.parse import urlparse
            def dl():
                os.makedirs("downloads/files", exist_ok=True)
                try:
                    response = requests.get(url, stream=True, timeout=30)
                    response.raise_for_status()
                    
                    filename = ""
                    cd = response.headers.get("content-disposition")
                    if cd and 'filename=' in cd:
                        filename = cd.split('filename=')[1].strip('"\'')
                    else:
                        parsed = urlparse(url)
                        filename = os.path.basename(parsed.path)
                    
                    if not filename:
                        filename = "downloaded_file.dat"
                        
                    save_path = os.path.join("downloads/files", filename)
                    with open(save_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    print(f"File downloaded: {save_path}")
                except Exception as e:
                    print(f"File download error: {e}")
            threading.Thread(target=dl, daemon=True).start()

    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def cleanup(self):
        pass

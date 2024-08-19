from PyQt5.QtWidgets import QMainWindow, QTableWidget, QPushButton, QVBoxLayout, QWidget, QTableWidgetItem, \
    QHeaderView, QAbstractItemView, QMessageBox,QProgressBar
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import os
import shutil
import platform
import subprocess

class ProgressBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")
        layout = QVBoxLayout(self)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

    def set_progress(self, value):
        self.progress_bar.setValue(value)

class DownloadManagerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Manager")
        self.setGeometry(150, 150, 600, 400)

        self.openMangaFolderButton = QPushButton("Open Manga Folder", self)
        self.openMangaFolderButton.clicked.connect(self.open_folder_manga)
        self.openMangaFolderButton.setFixedHeight(50)

        self.downloads_table = QTableWidget(self)
        # not editable
        self.downloads_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Add the progress bar column
        self.downloads_table.setColumnCount(4)
        self.downloads_table.setHorizontalHeaderLabels(["Manga", "Status", "Progress", ""])
        self.downloads_table.horizontalHeader().setStretchLastSection(True)

        # Set column resizing modes
        self.downloads_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Status column
        self.downloads_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)           # Progress column
        self.downloads_table.setColumnWidth(3, 50)                                                     # Button column

        self.downloads_table.horizontalHeader().setStretchLastSection(False)  # Ensure the last section doesn't stretch automatically

        # on double click on a row, open the manga folder
        self.downloads_table.cellDoubleClicked.connect(self.open_folder)

        layout = QVBoxLayout()
        layout.addWidget(self.openMangaFolderButton)
        layout.addWidget(self.downloads_table)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.downloads = {}

    def open_folder(self, row, column):
        manga_name = self.downloads_table.item(row, 0).text()
        folder_path = os.path.join(os.path.expanduser("~"), "Documents", "MangaDownloader", manga_name)
        system = platform.system()
        if system == "Windows":
            os.startfile(folder_path)
        elif system == "Darwin":  # macOS
            subprocess.call(["open", folder_path])
        elif system == "Linux":
            subprocess.call(["xdg-open", folder_path])
        else:
            print("Unsupported operating system")

    def open_folder_manga(self):
        folder_path = os.path.join(os.path.expanduser("~"), "Documents", "MangaDownloader")
        system = platform.system()
        if system == "Windows":
            os.startfile(folder_path)
        elif system == "Darwin":  # macOS
            subprocess.call(["open", folder_path])
        elif system == "Linux":
            subprocess.call(["xdg-open", folder_path])
        else:
            print("Unsupported operating system")

    def add_download(self, manga_name, download_thread):
        row_position = self.downloads_table.rowCount()
        self.downloads_table.insertRow(row_position)

        manga_item = QTableWidgetItem(manga_name)
        status_item = QTableWidgetItem("Starting...")
        progress_widget = ProgressBarWidget()
        trash_button = QPushButton()

        trash_button.setFixedWidth(50)
        trash_button.setIcon(QIcon(os.path.join(os.getcwd(),"src","img","trash.png")))
        trash_button.clicked.connect(lambda: self.remove_download(manga_name))

        self.downloads_table.setItem(row_position, 0, manga_item)
        self.downloads_table.setItem(row_position, 1, status_item)
        self.downloads_table.setCellWidget(row_position, 2, progress_widget)
        self.downloads_table.setCellWidget(row_position, 3, trash_button)

        # Track download in the downloads dict
        self.downloads[manga_name] = (row_position, download_thread, progress_widget)

        download_thread.status_update.connect(lambda status, row=row_position: self.update_status(row, status))
        download_thread.progress.connect(progress_widget.set_progress)
        download_thread.start()

    def update_status(self, row, status):
        # Ensure the row still exists before updating the status
        if self.downloads_table.item(row, 1):
            self.downloads_table.item(row, 1).setText(status)


    def remove_download(self, manga_name):
        reply = QMessageBox.question(self, 'Confirmation',
                                    f"Are you sure you want to delete the manga '{manga_name}'?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            row_position, download_thread, progress_widget = self.downloads.get(manga_name, (None, None, None))
            if row_position is not None:
                # Stop the thread
                download_thread.stop()

                # Disconnect signals to prevent further emissions
                try:
                    download_thread.status_update.disconnect()
                    download_thread.progress.disconnect()
                except Exception as e:
                    print(f"Error while disconnecting signals: {e}")

                # Remove the corresponding row and the folder
                folder_path = os.path.join(os.path.expanduser("~"), "Documents", "MangaDownloader", manga_name)
                shutil.rmtree(folder_path, ignore_errors=True)
                self.downloads_table.removeRow(row_position)
                del self.downloads[manga_name]
                self.downloads_table.repaint()


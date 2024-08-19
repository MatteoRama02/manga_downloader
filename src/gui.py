from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import os
from src.splash_screen import SplashScreen
from src.download_thread import DownloadThread
from src.download_manager import DownloadManagerWindow
from src.carousel_widget import CarouselWidget
from src.manga_selection_dialog import MangaSelectionDialog
from src.utilities import prevent_sleep, restore_sleep, choose_manga
import sys
from src.scraper.mangaworld_downloader import research_manga, research_thumbnails
from src.scraper.comick_downloader import research_manga_comick
from pyqttoast import Toast, ToastPreset, ToastPosition




class MyWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.tray_icon = QSystemTrayIcon(QIcon('icon.jpg'), self)
        self.tray_icon.setVisible(True)  # Make sure the icon is visible
        self.initUI()
        self.download_manager = DownloadManagerWindow()
        self.setup_shortcuts()
        
	if not os.path.exists(os.path.join(os.path.expanduser("~"), "Documents", "MangaDownloader"):
        	os.mkdir(os.path.join(os.path.expanduser("~"), "Documents", "MangaDownloader")


        # Initialize choose as an instance variable
        self.choose = "MangaWorld - IT"  # Default value

    def setup_shortcuts(self):
        # Create a shortcut for Ctrl+Q to close the window
        close_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        close_shortcut.activated.connect(self.close)

    def initUI(self):
        # Set the title and size of the window
        self.setWindowTitle("MangaWorld Downloader")
        self.setGeometry(100, 100, 850, 550)

        # Center the window
        self.center()

        # Create a central widget and set it as the central widget of the main window
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Create a vertical layout to center the horizontal layout
        main_layout = QVBoxLayout(central_widget)

        # Title label
        titolo = QLabel("MangaWorld Downloader", self)
	
	

        # Combobox
        combobox = QComboBox(self)
        combobox.addItem("MangaWorld - IT")
        combobox.addItem("Comick - EN")

        # On combobox change, update the selected value
        combobox.currentIndexChanged.connect(lambda: self.choose_manga_site(combobox.currentText()))
        
        title_img_layout = QHBoxLayout()
        title_img_layout.addWidget(combobox, alignment=Qt.AlignCenter)
        title_img_layout.addWidget(titolo, alignment=Qt.AlignCenter)

        h_layout = QHBoxLayout()
        v_layout = QVBoxLayout()

        label = QLabel("Insert manga name:", self)
        v_layout.addWidget(label, alignment=Qt.AlignCenter)

        self.line_edit = QLineEdit(self, minimumWidth=200)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.line_edit, alignment=Qt.AlignCenter)
        v_layout.addSpacing(10)

        self.button = QPushButton("Download", self)
        self.button.clicked.connect(self.start_download)
        self.line_edit.returnPressed.connect(self.button.click)

        v_layout.addWidget(self.button, alignment=Qt.AlignCenter)
        h_layout.addLayout(v_layout)

        limit = 6

        # Fetch URLs
        urls = research_thumbnails()

        trending_label_layout = QVBoxLayout()
        trending_label = QLabel("Top best score manga:", self)
        trending_label_layout.addWidget(trending_label, alignment=Qt.AlignCenter)

        carousel_layout = QVBoxLayout()

        # Create and add the carousel widget
        self.carousel_widget = CarouselWidget(urls)
        self.carousel_widget.thumbnail_clicked.connect(self.handle_thumbnail_click)  # Connect to the new slot
        carousel_layout.addWidget(self.carousel_widget)

        main_layout.addLayout(title_img_layout)
        main_layout.addSpacing(20)
        main_layout.addLayout(h_layout)
        main_layout.addSpacing(30)
        main_layout.addLayout(trending_label_layout)
        main_layout.addLayout(carousel_layout)

        self.download_manager_button = QPushButton("Open Download Manager", self)
        self.download_manager_button.clicked.connect(self.open_download_manager)
        self.download_manager_button.setFixedHeight(50)
        main_layout.addWidget(self.download_manager_button)
    
    def choose_manga_site(self, value):
        # Update the instance variable
        self.choose = value
        print(f"Selected site: {self.choose}")  # For debugging purposes
    
    # Shows a toast notification every time the button is clicked
    def show_toast(self, titolo, messaggio, preset=ToastPreset.SUCCESS):
        toast = Toast(self)
        font = QFont('Times', 20, QFont.Weight.Bold)
        toast.setTitleFont(font)
        toast.setTextFont(font)
        toast.setPosition(ToastPosition.TOP_RIGHT)
        toast.setDuration(5000)
        toast.setTitle(titolo)
        toast.setText(messaggio)
        toast.applyPreset(preset)
        toast.show()
    
    def center(self):
        screen = QDesktopWidget().availableGeometry().center()
        frame_geo = self.frameGeometry()
        frame_geo.moveCenter(screen)
        self.move(frame_geo.topLeft())

    def start_download(self):
        manga_name = self.line_edit.text()
        if not manga_name:
            QMessageBox.critical(self, "Error", "Please insert a manga name")
            return

        # Get the selected combobox value from the instance variable
        combobox_value = self.choose

        try:
            
            # Switch combobox value
            if combobox_value == "MangaWorld - IT":
                manga_dict = research_manga(manga_name)
            else:
                manga_dict = research_manga_comick(manga_name)
        except Exception as e:
            QMessageBox.critical(self, "Error", e.__str__())
            return

        if not manga_dict:
            QMessageBox.critical(self, "Error", "Manga not found")
            return

        if len(manga_dict) == 1:
            selected_manga = list(manga_dict.keys())[0]
            self.download_thread = DownloadThread(manga_name, selected_manga, manga_dict,self.choose, parent=self)
            self.download_thread.progress.connect(self.update_progress)
            self.download_thread.status_update.connect(self.handle_status_update)
            self.download_thread.start()
            self.download_manager.add_download(selected_manga, self.download_thread)
            self.show_toast("Download Started", f"Downloading manga: {selected_manga}")
            return

        dialog = MangaSelectionDialog(manga_dict, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_manga = dialog.selected_manga
            self.download_thread = DownloadThread(manga_name, selected_manga, manga_dict,self.choose, parent=self)
            self.download_thread.progress.connect(self.update_progress)
            self.download_thread.status_update.connect(self.handle_status_update)
            self.download_thread.start()
            self.download_manager.add_download(selected_manga, self.download_thread)
            self.show_toast("Download Started", f"Downloading manga: {selected_manga}")
        else:
            QMessageBox.information(self, "Cancelled", "No manga selected.")

    def handle_status_update(self, status):
        self.show_toast("Download Status", status)
        if status == "Download completed":
            pass

    def open_download_manager(self):
        self.download_manager.show()

    def update_progress(self, value):
        print(f"Progress: {value}%")

    def handle_thumbnail_click(self, title):
        manga_dict = research_manga(title)

        if not manga_dict:
            QMessageBox.critical(self, "Error", "Manga not found")
            return

        if len(manga_dict) == 1:
            selected_manga = list(manga_dict.keys())[0]
            self.download_thread = DownloadThread(title, selected_manga, manga_dict, parent=self)
            self.download_thread.progress.connect(self.update_progress)
            self.download_thread.status_update.connect(self.handle_status_update)
            self.download_thread.start()
            self.download_manager.add_download(selected_manga, self.download_thread)
            self.show_toast("Download Started", f"Downloading manga: {selected_manga}")
        else:
            dialog = MangaSelectionDialog(manga_dict, self)
            if dialog.exec_() == QDialog.Accepted:
                selected_manga = dialog.selected_manga
                self.download_thread = DownloadThread(title, selected_manga, manga_dict, parent=self)
                self.download_thread.progress.connect(self.update_progress)
                self.download_thread.status_update.connect(self.handle_status_update)
                self.download_thread.start()
                self.download_manager.add_download(selected_manga, self.download_thread)
                self.show_toast("Download Started", f"Downloading manga: {selected_manga}")
            else:
                QMessageBox.information(self, "Cancelled", "No manga selected.")

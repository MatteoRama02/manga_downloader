import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap,QIcon,QFont
import requests
from pyqttoast import Toast, ToastPreset, ToastPosition
from mangaworld_downloader import research_thumbnails,research_manga, volumes_with_chapter_link, create_data_volumes_folders, download_volumes_images, create_pdf, remove_data_folder,number_of_images_in_chapter,download_chapter_images


class SplashScreen(QSplashScreen):
    def __init__(self, pixmap, parent=None):
        super().__init__(pixmap, Qt.WindowStaysOnTopHint, parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("background: transparent;")
        self.show()
   
    def show_message(self, message):
        self.showMessage(message, Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        
class DownloadThread(QThread):
    progress = pyqtSignal(int)
    status_update = pyqtSignal(str)  # New signal for status updates

    def __init__(self, manga_name, selectedManga, mangaDict, parent=None):
        super().__init__(parent)
        self.manga_name = manga_name
        self.selectedManga = selectedManga
        self.mangaDict = mangaDict
        self.parent = parent

    def run(self):
        selected_manga = self.selectedManga
        manga_dict = self.mangaDict
        
        if not selected_manga:
            self.status_update.emit("User canceled the selection")
            return

        vol_chap_dict = volumes_with_chapter_link(manga_dict[selected_manga])
        create_data_volumes_folders(selected_manga, vol_chap_dict)

        total_chapters = sum(len(chaps) for chaps in vol_chap_dict.values())
        current_chapter = 0

        for i, (vol_name, chapters) in enumerate(vol_chap_dict.items()):
            for j, chap_link in enumerate(chapters):
                # Update status
                self.status_update.emit(f"Downloading {vol_name} Chapter {j + 1}")

                # Perform the download operation
                number_of_images = number_of_images_in_chapter(chap_link)
                download_chapter_images(chap_link, i, str(j), selected_manga, number_of_images)

                # Update progress
                current_chapter += 1
                self.progress.emit(int((current_chapter / total_chapters) * 100))

        create_pdf(selected_manga)

        remove_data_folder(selected_manga)
        self.status_update.emit("Download completed")
        # make a sound when the download is completed
        os.system("aplay sound.wav")


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tray_icon = QSystemTrayIcon(QIcon('icon.jpg'), self)
        self.tray_icon.setVisible(True)  # Make sure the icon is visible

        self.initUI()
        self.download_manager = DownloadManagerWindow()


    def initUI(self):
        # Set the title and size of the window
        self.setWindowTitle("MangaWorld Downloader")
        self.setGeometry(100, 100, 500, 450)

        # Center the window
        self.center()

        # Create a central widget and set it as the central widget of the main window
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Create a vertical layout to center the horizontal layout
        main_layout = QVBoxLayout(central_widget)

        # Title label
        titolo = QLabel("MangaWorld Downloader", self)

        # Image label
        img = QLabel(self)
        pixmap = QPixmap('MangaWorldLogo.svg')

        if not pixmap.isNull():
            pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img.setPixmap(pixmap)
        else:
            print("Failed to load image")

        title_img_layout = QHBoxLayout()
        title_img_layout.addWidget(img, alignment=Qt.AlignCenter)
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


        urls = research_thumbnails()

        trending_label_layout = QVBoxLayout()
        trending_label = QLabel("Trending now:", self)
        trending_label_layout.addWidget(trending_label, alignment=Qt.AlignCenter)

        carousel_layout = QHBoxLayout()

        for title, url in list(urls.items())[:5]:  # Get the first 5 entries
            label = QLabel(self)
            
            # Load the image data
            pixmap = QPixmap()
            pixmap.loadFromData(requests.get(url).content)
            
            if not pixmap.isNull():
                pixmap = pixmap.scaled(100, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(pixmap)
            else:
                print("Failed to load image")
            
            # Set the tooltip with the title
            label.setToolTip(title)
            
            # Set the size policy
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            # Add the label to the layout
            carousel_layout.addWidget(label, alignment=Qt.AlignCenter)


        main_layout.addLayout(title_img_layout)
        main_layout.addSpacing(20)
        main_layout.addLayout(h_layout)
        main_layout.addSpacing(30)
        main_layout.addLayout(trending_label_layout)
        main_layout.addLayout(carousel_layout)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")

        main_layout.addWidget(self.progress_bar)
        # Add a button to open the Download Manager
        self.download_manager_button = QPushButton("Open Download Manager", self)
        self.download_manager_button.clicked.connect(self.open_download_manager)
        main_layout.addWidget(self.download_manager_button)
    # Shows a toast notification every time the button is clicked
    def show_toast(self,titolo, messaggio, preset=ToastPreset.SUCCESS ):
        toast = Toast(self)
             # Init font
        # Init font
        font = QFont('Times', 20, QFont.Weight.Bold)

        # Set fonts
        toast.setTitleFont(font)  # Default: QFont('Arial', 9, QFont.Weight.Bold)
        toast.setTextFont(font)   # Default: QFont('Arial', 9)
        toast.setPosition(ToastPosition.TOP_RIGHT)  # Default: ToastPosition.BOTTOM_RIGHT
        toast.setDuration(5000)  # Hide after 5 seconds
        toast.setTitle(titolo)
        toast.setText(messaggio)
        toast.applyPreset(preset)  # Apply style preset
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
        
        manga_dict = research_manga(manga_name)
        
        if not manga_dict:
            QMessageBox.critical(self, "Error", "Manga not found")
            return
        
        if len(manga_dict) == 1:
            selected_manga = list(manga_dict.keys())[0]
            self.download_thread = DownloadThread(manga_name, selected_manga, manga_dict, parent=self)
            self.download_thread.progress.connect(self.update_progress)
            self.download_thread.start()
            self.download_manager.add_download(selected_manga, self.download_thread)
            self.show_toast("Download Started", f"Downloading manga: {selected_manga}")
            return
        
        # Show the MangaSelectionDialog to the user
        dialog = MangaSelectionDialog(manga_dict, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_manga = dialog.selected_manga
            self.download_thread = DownloadThread(manga_name, selected_manga, manga_dict, parent=self)
            self.download_thread.progress.connect(self.update_progress)
            self.download_thread.start()
            self.download_manager.add_download(selected_manga, self.download_thread)
            self.show_notification("Download Started", f"Downloading manga: {selected_manga}")

        else:
            # Handle the case where the user cancels the dialog
            QMessageBox.information(self, "Cancelled", "No manga selected.")

    def open_download_manager(self):
        self.download_manager.show()
    def update_progress(self, value):
        self.progress_bar.setValue(value)

class DownloadManagerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Manager")
        self.setGeometry(150, 150, 600, 400)

        self.downloads_table = QTableWidget(self)
        self.downloads_table.setColumnCount(2)
        self.downloads_table.setHorizontalHeaderLabels(["Manga", "Status"])
        self.downloads_table.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout()
        layout.addWidget(self.downloads_table)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.downloads = {}

    def add_download(self, manga_name, download_thread):
        row_position = self.downloads_table.rowCount()
        self.downloads_table.insertRow(row_position)

        manga_item = QTableWidgetItem(manga_name)
        status_item = QTableWidgetItem("Starting...")

        self.downloads_table.setItem(row_position, 0, manga_item)
        self.downloads_table.setItem(row_position, 1, status_item)

        # Track download in the downloads dict
        self.downloads[manga_name] = (row_position, download_thread)

        download_thread.status_update.connect(lambda status, row=row_position: self.update_status(row, status))
        download_thread.progress.connect(lambda progress, row=row_position: self.update_progress(row, progress))

    def update_status(self, row, status):
        self.downloads_table.setItem(row, 1, QTableWidgetItem(status))

    def update_progress(self, row, progress):
        self.downloads_table.setItem(row, 1, QTableWidgetItem(f"In progress: {progress}%"))
    

class MangaSelectionDialog(QDialog):
    def __init__(self, manga_dict, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Select a Manga")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout(self)

        # Create a label to instruct the user
        label = QLabel("Please choose a manga:", self)
        layout.addWidget(label, alignment=Qt.AlignCenter)

        # Create a scroll area to hold the manga buttons
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)

        # Create a widget to act as a container for the buttons
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)

        # Generate buttons for each manga in the dictionary
        self.selected_manga = None
        for manga_name in manga_dict.keys():
            button = QPushButton(manga_name, self)
            button.clicked.connect(lambda checked, name=manga_name: self.select_manga(name))
            button_layout.addWidget(button)

        scroll_area.setWidget(button_container)
        layout.addWidget(scroll_area)

        # Set the layout of the dialog
        self.setLayout(layout)

    def select_manga(self, manga_name):
        self.selected_manga = manga_name
        self.accept()

def choose_manga(manga_dict):
    # Create an instance of the dialog
    dialog = MangaSelectionDialog(manga_dict)

    # Execute the dialog and check if the user has selected a manga
    if dialog.exec_() == QDialog.Accepted:
        return dialog.selected_manga
    else:
        return None

app = QApplication(sys.argv)
window = MyWindow()
window.show()
sys.exit(app.exec_())

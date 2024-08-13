import shutil
import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal,QTimer,QSize
from PyQt5.QtGui import QPixmap,QIcon,QFont
import requests
from pyqttoast import Toast, ToastPreset, ToastPosition
from mangaworld_downloader import research_thumbnails,research_manga, volumes_with_chapter_link, create_data_volumes_folders, download_volumes_images, create_pdf, remove_data_folder,number_of_images_in_chapter,download_chapter_images
import platform
import pygame
import os
import subprocess
import platform
 
def prevent_sleep():
    if platform.system() == "Windows":
        import ctypes
        # Prevents the system from entering sleep or turning off the display
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)
    elif platform.system() == "Darwin":  # macOS
        import subprocess
        # Prevents the system from sleeping
        subprocess.call('caffeinate', shell=True)
    # On Linux, this is typically managed by the system, and there is no simple standard way to handle it.
    
def restore_sleep():
    if platform.system() == "Windows":
        import ctypes
        # Restores the system's ability to sleep or turn off the display
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
    elif platform.system() == "Darwin":  # macOS
        # No need for specific actions; 'caffeinate' exits when the app is closed
        pass
    
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
    status_update = pyqtSignal(str)  # Signal for status updates

    def __init__(self, manga_name, selectedManga, mangaDict, parent=None):
        super().__init__(parent)
        self.manga_name = manga_name
        self.selectedManga = selectedManga
        self.mangaDict = mangaDict
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

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
            if self._stop_flag:
                self.status_update.emit("Download canceled")
                return

            for j, chap_link in enumerate(chapters):
                if self._stop_flag:
                    self.status_update.emit("Download canceled")
                    return
                
                number_of_images = number_of_images_in_chapter(chap_link)
                download_chapter_images(chap_link, i, str(j), selected_manga, number_of_images)

                current_chapter += 1
                self.progress.emit(int((current_chapter / total_chapters) * 100))

        if self._stop_flag:
            self.status_update.emit("Download canceled")
            return

        self.status_update.emit(f"Generating PDFs...")
        create_pdf(selected_manga)
        remove_data_folder(selected_manga)
        self.status_update.emit(f"PDFs generated!")
        
        if self._stop_flag:
            return
        
        # Play sound when download is completed
        pygame.mixer.init()
        pygame.mixer.music.load('src/sounds/finish.mp3')
        pygame.mixer.music.play()

        # Check the stop flag during sound playback
        while pygame.mixer.music.get_busy():
            if self._stop_flag:
                pygame.mixer.music.stop()
                break
            pygame.time.Clock().tick(10)

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

        # Image label
        img = QLabel(self)
        os.chdir(os.path.dirname(__file__))
        pixmap = QPixmap('src/img/MangaWorldLogo.svg')

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
        
    # Shows a toast notification every time the button is clicked
    def show_toast(self,titolo, messaggio, preset=ToastPreset.SUCCESS):
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
        
        manga_dict = research_manga(manga_name)
        
        if not manga_dict:
            QMessageBox.critical(self, "Error", "Manga not found")
            return
        
        if len(manga_dict) == 1:
            selected_manga = list(manga_dict.keys())[0]
            self.download_thread = DownloadThread(manga_name, selected_manga, manga_dict, parent=self)
            self.download_thread.progress.connect(self.update_progress)
            self.download_thread.status_update.connect(self.handle_status_update)
            self.download_thread.start()
            self.download_manager.add_download(selected_manga, self.download_thread)
            self.show_toast("Download Started", f"Downloading manga: {selected_manga}")
            return
        
        dialog = MangaSelectionDialog(manga_dict, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_manga = dialog.selected_manga
            self.download_thread = DownloadThread(manga_name, selected_manga, manga_dict, parent=self)
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
        self.downloads_table.setHorizontalHeaderLabels(["Manga", "Status", "Progress",""])
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
        folder_path = os.path.join(os.path.expanduser("~"), "Documents", "MangaDownloader",  manga_name)
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
        trash_button.setIcon(QIcon("src/img/trash.png"))
        trash_button.clicked.connect(lambda: self.remove_download(manga_name))

        self.downloads_table.setItem(row_position, 0, manga_item)
        self.downloads_table.setItem(row_position, 1, status_item)
        self.downloads_table.setCellWidget(row_position, 2, progress_widget)
        self.downloads_table.setCellWidget(row_position, 3, trash_button)

        # Track download in the downloads dict
        self.downloads[manga_name] = (row_position, download_thread, progress_widget)

        download_thread.status_update.connect(lambda status, row=row_position: self.update_status(row, status))
        download_thread.progress.connect(lambda progress, row=row_position: self.update_progress(row, progress))

    def update_status(self, row, status):
        item = self.downloads_table.item(row, 1)
        if item is not None:
            item.setText(status)
        else:
            print(f"Warning: Attempted to update status for a row {row} that does not exist or has been removed.")


    def update_progress(self, row, progress):
        if row < 0 or row >= self.downloads_table.rowCount():
            return  # Avoid accessing a row that doesn't exist

        item = self.downloads_table.item(row, 0)
        if item is None:
            return  # Avoid accessing a non-existent item

        progress_widget = self.downloads.get(item.text())
        if progress_widget:
            progress_widget[2].set_progress(progress)

    def remove_download(self, manga_name):
        
        # Confirm the user wants to remove the download
        reply = QMessageBox.question(self, "Remove Download", f"Are you sure you want to remove the download for {manga_name}?", QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.No:
            return
        else: 
            row, download_thread, progress_widget = self.downloads[manga_name]
            download_thread.stop()
            self.downloads_table.removeRow(row)
            #wait the kill of the thread
            download_thread.wait()
            try:
                # Remove the manga folder in documents if it exist even if it has files
                shutil.rmtree(os.path.join(os.path.expanduser("~"), "Documents", "MangaDownloader", manga_name))
            except FileNotFoundError:
                pass
            
            try:
                shutil.rmtree(os.path.join("Data", manga_name))
            except FileNotFoundError:
                pass
            
            del self.downloads[manga_name]

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
    
    
    
    
class CarouselWidget(QWidget):
    thumbnail_clicked = pyqtSignal(str)  # Signal to emit when a thumbnail is clicked

    def __init__(self, urls, max_items=6, image_size=(120, 200), parent=None):
        super().__init__(parent)
        
        self.urls = urls
        self.max_items = max_items
        self.image_size = image_size
        self.current_index = 0
        
        self.init_ui()
        
        # Set up a timer to handle the animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_carousel)
        self.timer.start(30000)  # Update every 30 seconds

    def init_ui(self):
        self.layout = QHBoxLayout(self)
        self.buttons = []

        # Create QPushButton widgets for the carousel
        for _ in range(self.max_items):
            button = QPushButton(self)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            button.clicked.connect(self.on_thumbnail_clicked)
            self.buttons.append(button)
            self.layout.addWidget(button, alignment=Qt.AlignCenter)

        self.update_carousel()

    def update_carousel(self):
        keys = list(self.urls.keys())
        num_urls = len(keys)

        # Clear current images
        for button in self.buttons:
            button.setIcon(QIcon())  # Clear the icon
            button.setToolTip("")  # Clear the tooltip

        # Update image buttons with the current set of 6 images
        for i in range(self.max_items):
            # Calculate the index for the current image
            index = (self.current_index + i) % num_urls
            title = keys[index]
            url = self.urls[title]
            
            # Load the image data
            pixmap = QPixmap()
            pixmap.loadFromData(requests.get(url).content)
            
            if not pixmap.isNull():
                pixmap = pixmap.scaled(*self.image_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon = QIcon(pixmap)
                self.buttons[i].setIcon(icon)
                self.buttons[i].setIconSize(QSize(*self.image_size))
                self.buttons[i].setToolTip(title)
            else:
                self.buttons[i].setToolTip("Failed to load image")

        # Move to the next index, ensuring wrap-around
        self.current_index = (self.current_index + self.max_items) % num_urls

    def on_thumbnail_clicked(self):
        button = self.sender()
        title = button.toolTip()
        self.thumbnail_clicked.emit(title) 
        
        
app = QApplication(sys.argv)

window = MyWindow()
window.show()
sys.exit(app.exec_())

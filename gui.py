import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from mangaworld_downloader import research_manga, volumes_with_chapter_link, create_data_volumes_folders, download_volumes_images, create_pdf, remove_data_folder,number_of_images_in_chapter,download_chapter_images


class DownloadThread(QThread):
    progress = pyqtSignal(int)

    def __init__(self, manga_name,selectedManga,mangaDict, parent=None):
        self.selectedManga = selectedManga
        self.mangaDict = mangaDict
        super().__init__(parent)
        self.manga_name = manga_name
        self.parent = parent  # Reference to the main window

    def run(self):
        selected_manga = self.selectedManga
        manga_dict = self.mangaDict
        
        if not selected_manga:
            # User canceled the selection
            return

        vol_chap_dict = volumes_with_chapter_link(manga_dict[selected_manga])

        create_data_volumes_folders(selected_manga, vol_chap_dict)

        total_chapters = sum(len(chaps) for chaps in vol_chap_dict.values())

        for i, (vol_name, chapters) in enumerate(vol_chap_dict.items()):
            for j, chap_link in enumerate(chapters):
                # Perform the download operation
                number_of_images = number_of_images_in_chapter(chap_link)
                download_chapter_images(chap_link, i, str(j), selected_manga, number_of_images)
                
                # Update progress
                self.progress.emit(int(((i + 1) / total_chapters) * 100))

        create_pdf(vol_chap_dict, selected_manga)
        remove_data_folder()

    def choose_manga(self, manga_dict):
        # Show the selection dialog to the user
        dialog = MangaSelectionDialog(manga_dict, self.parent)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.selected_manga
        return None


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

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

        trending_label_layout = QVBoxLayout()
        trending_label = QLabel("Trending now:", self)
        trending_label_layout.addWidget(trending_label, alignment=Qt.AlignCenter)

        carousel_layout = QHBoxLayout()

        for _ in range(5):
            label = QLabel()
            pixmap = QPixmap('img1.jpg')
            if not pixmap.isNull():
                pixmap = pixmap.scaled(100, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(pixmap)
            else:
                print("Failed to load image")

            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
        
        # Show the MangaSelectionDialog to the user
        dialog = MangaSelectionDialog(manga_dict, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_manga = dialog.selected_manga
            self.download_thread = DownloadThread(manga_name, selected_manga, manga_dict, parent=self)
            self.download_thread.progress.connect(self.update_progress)
            self.download_thread.start()
        else:
            # Handle the case where the user cancels the dialog
            QMessageBox.information(self, "Cancelled", "No manga selected.")


    def update_progress(self, value):
        self.progress_bar.setValue(value)


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

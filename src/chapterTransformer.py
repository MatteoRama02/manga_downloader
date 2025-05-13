from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import os
import sys
from src.splash_screen import SplashScreen
from src.download_thread import DownloadThread
from src.download_manager import DownloadManagerWindow
from src.carousel_widget import CarouselWidget
from src.manga_selection_dialog import MangaSelectionDialog
from src.utilities import prevent_sleep, restore_sleep, choose_manga
from src.scraper.mangaworld_downloader import research_manga, research_thumbnails
from src.scraper.comick_downloader import research_manga_comick
from pyqttoast import Toast, ToastPreset, ToastPosition


class MangaToPdf(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manga to PDF")
        self.setGeometry(150, 150, 600, 200)

        self.manga_folder = ""

        # Central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Layouts
        main_layout = QVBoxLayout()
        input_layout = QHBoxLayout()
        button_layout = QHBoxLayout()

        # Folder input
        self.manga_folder_input = QLineEdit(self)
        self.manga_folder_input.setPlaceholderText("Manga Folder")
        self.manga_folder_input.setReadOnly(True)
        self.manga_folder_input.setAlignment(Qt.AlignCenter)
        self.manga_folder_input.setFixedHeight(50)

        # Folder button
        self.openMangaFolderButton = QPushButton("Select Manga Folder", self)
        self.openMangaFolderButton.clicked.connect(self.open_folder_manga)
        self.openMangaFolderButton.setFixedHeight(50)
        self.openMangaFolderButton.setFixedWidth(200)

        # Convert button
        self.convertButton = QPushButton("Convert to PDF", self)
        self.convertButton.clicked.connect(self.convert_to_pdf)
        self.convertButton.setFixedHeight(50)
        self.convertButton.setFixedWidth(200)
        self.convertButton.setEnabled(False)

        # Add widgets to layouts
        input_layout.addWidget(self.manga_folder_input)
        input_layout.addWidget(self.openMangaFolderButton)

        button_layout.addStretch()
        button_layout.addWidget(self.convertButton)
        button_layout.addStretch()

        main_layout.addStretch()
        main_layout.addLayout(input_layout)
        main_layout.addSpacing(20)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()

        central_widget.setLayout(main_layout)

    def open_folder_manga(self):
        
        folder = QFileDialog.getExistingDirectory(self, "Select Manga Folder")
        if folder:
            self.manga_folder = folder
            self.manga_folder_input.setText(folder)
            self.manga_folder_input.setStyleSheet("QLineEdit { background-color: lightgreen; }")
            self.openMangaFolderButton.setText("Manga Folder Selected")
            self.convertButton.setEnabled(True)
        else:
            self.manga_folder_input.setText("")
            self.manga_folder_input.setStyleSheet("QLineEdit { background-color: lightcoral; }")
            self.openMangaFolderButton.setText("Select Manga Folder")
            self.convertButton.setEnabled(False)
            
            
    def convert_to_pdf(self):
        import os
        import io
        from PIL import Image
        from PyPDF2 import PdfMerger
        import re

        manga_folders = sorted([f for f in os.listdir(self.manga_folder) if os.path.isdir(os.path.join(self.manga_folder, f))])
        if not manga_folders:
            Toast("No manga folders found", preset=ToastPreset.ERROR, position=ToastPosition.BOTTOM).show()
            return

        final_pdf_path = os.path.join(self.manga_folder, "Manga_Completo.pdf")
        merger = PdfMerger()

        for manga_folder in manga_folders:
            manga_path = os.path.join(self.manga_folder, manga_folder)

            for root, dirs, files in os.walk(manga_path):
                files.sort(key=lambda x: (int(re.search(r'(\d+)', x).group(0)) if re.search(r'(\d+)', x) else float('inf'), x))
                
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
                        image_path = os.path.join(root, file)

                        try:
                            image = Image.open(image_path).convert("RGB")
                            img_byte_arr = io.BytesIO()
                            image.save(img_byte_arr, format='PDF')
                            img_byte_arr.seek(0)
                            merger.append(img_byte_arr)
                        except Exception as e:
                            print(f"Errore nel convertire l'immagine {file}: {e}")

        if merger.pages:
            merger.write(final_pdf_path)
            QMessageBox.information(self, "Success", f"PDF creato: {final_pdf_path}")
        else:
            QMessageBox.warning(self, "Warning", f"Nessuna immagine valida trovata.")
        
        merger.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MangaToPdf()
    window.show()
    sys.exit(app.exec_())

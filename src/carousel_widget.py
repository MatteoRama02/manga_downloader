from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import *
import requests
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


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
        
        
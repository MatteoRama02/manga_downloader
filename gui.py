import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()



        # Set the title and size of the window
        self.setWindowTitle("PyQt5 Centered Horizontal Buttons")
        self.setGeometry(100, 100, 500, 400)

        #block resizing
        self.setFixedSize(500, 450)
        

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
        
        # Check if the pixmap is loaded correctly
        if not pixmap.isNull():
            # Resize the pixmap (e.g., width=50, height=50)
            pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img.setPixmap(pixmap)
        else:
            print("Failed to load image")

        # Create a horizontal layout to hold the title and image side by side
        title_img_layout = QHBoxLayout()
        title_img_layout.addWidget(img, alignment=Qt.AlignCenter)
        title_img_layout.addWidget(titolo, alignment=Qt.AlignCenter)
        
        # Create a horizontal layout for buttons
        h_layout = QHBoxLayout()

        v_layout = QVBoxLayout() # Vertical layout for buttons and label

        # Create a label with Insert manga name
        label = QLabel("Insert manga name:", self)
        v_layout.addWidget(label, alignment=Qt.AlignCenter)

        # Create a line edit widget
        self.line_edit = QLineEdit(self, minimumWidth=200)
        v_layout.addSpacing(10)
        

        v_layout.addWidget(self.line_edit, alignment=Qt.AlignCenter)

        v_layout.addSpacing(10)

        # Create a button widget
        self.button = QPushButton("Download", self)
        v_layout.addWidget(self.button, alignment=Qt.AlignCenter)


        h_layout.addLayout(v_layout)

        trending_label_layout = QVBoxLayout()
        trending_label = QLabel("Trending now:", self)
        trending_label_layout.addWidget(trending_label, alignment=Qt.AlignCenter)

        carousel_layout = QHBoxLayout()
 
        
        # Create separate QLabel instances
        for _ in range(5):
            label = QLabel()
            pixmap = QPixmap('img1.jpg')
            if not pixmap.isNull():
                pixmap = pixmap.scaled(100, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(pixmap)
            else:
                print("Failed to load image")
            
            # Optionally, set a size policy to ensure the QLabel expands
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            carousel_layout.addWidget(label, alignment=Qt.AlignCenter)
        # Add layouts to the main vertical layout
        main_layout.addLayout(title_img_layout)
        #make a space between the title and the buttons
        main_layout.addSpacing(20)
        main_layout.addLayout(h_layout)
        main_layout.addSpacing(30)
        main_layout.addLayout(trending_label_layout)
        main_layout.addLayout(carousel_layout)

        # Create a progress bar and add it to the main layout
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setValue(30)
        
        # set green
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")

        main_layout.addWidget(self.progress_bar)


# Create an application instance
app = QApplication(sys.argv)

# Create an instance of your window
window = MyWindow()

# Show the window
window.show()

# Execute the application's main loop
sys.exit(app.exec_())
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton, QAbstractItemView

class MangaSelectionDialog(QDialog):
    def __init__(self, manga_dict, parent=None):
        super().__init__(parent)
        self.manga_dict = manga_dict
        self.selected_manga = None

        self.setWindowTitle("Select Manga")
        self.setGeometry(300, 300, 400, 300)

        layout = QVBoxLayout()

        self.label = QLabel("Select a manga from the list below:")
        layout.addWidget(self.label)

        self.list_widget = QListWidget(self)
        self.list_widget.addItems(self.manga_dict.keys())
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.list_widget)

        self.select_button = QPushButton("Select", self)
        self.select_button.clicked.connect(self.select_manga)
        layout.addWidget(self.select_button)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    def select_manga(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            self.selected_manga = selected_items[0].text()
            self.accept()
        else:
            self.reject()

    def get_selected_manga(self):
        return self.selected_manga

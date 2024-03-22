from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QSpacerItem, QSizePolicy, QMainWindow
from PyQt5.QtGui import QCloseEvent, QMovie
from PyQt5.QtCore import Qt, QSize

from logger import get_logger

_LOGGER = get_logger(__name__)

class LoadingWindowManager:
    def __init__(self, main_window):
        self.loading_window = None
        self.main_window = main_window
    
    def show_usb_window(self):
        message = "Подключаемся к плате..."
        self._show_window(message)

    def show_calibration_window(self):
        message = "Начинаем калибровку..."
        self._show_window(message)

    def _show_window(self, message: str):
        self.loading_window = LoadingWindow(self.main_window, message)
        self.loading_window.show()

    def close_window(self):
        if self.loading_window is not None:
            _LOGGER.debug("Close loading window")
            self.loading_window.close()
            self.loading_window = None
    
    def follow_parent(self):
        if self.loading_window is not None:
            self.loading_window.place_on_parent()
            self.raise_on_top()
    
    def raise_on_top(self):
        if self.loading_window is not None:
            self.loading_window.raise_()


class LoadingWindow(QWidget):
    def __init__(self, parent, message: str):
        super().__init__()
        self.parent_window = parent
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: lightgrey;")
        self.setFixedSize(250, 100)

        layout = QVBoxLayout()
        self.setLayout(layout)

        label_text = QLabel(message)
        label_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_text)

        spacer = QSpacerItem(40, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addItem(spacer)

        self.movie = QMovie("app/assets/loading.gif")
        self.movie.setScaledSize(QSize(50, 50))
        self.label = QLabel()
        self.label.setMovie(self.movie)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.movie.start()

    def showEvent(self, event):
        super().showEvent(event)
        _LOGGER.debug(f"Parent pos: {self.parent_window.pos()}, current pos: {self.rect().center()}, move: {self.parent_window.pos() - self.rect().center()}")
        self.place_on_parent()

    def place_on_parent(self):
        parent_center = self.parent_window.pos() + self.parent_window.rect().center()
        self.move(parent_center - self.rect().center())


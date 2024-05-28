from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QBrush, QColor, QFont, QPainterPath
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QMainWindow


class BaseWindow(QMainWindow):
    def __init__(self, title, width, height):
        """
        Initialize the base window.
        """
        super().__init__()
        self.initUI(title, width, height)
        self.setWindowPosition()
        self.is_dragging = False

    def initUI(self, title, width, height):
        """
        Initialize the user interface.
        """
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(width, height)

        self.main_widget = QWidget(self)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        title_layout = QHBoxLayout()
        title_label = QLabel('WhisperWriter')
        title_label.setFont(QFont('Segoe UI', 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)

        close_button = QPushButton('X')
        close_button.setFixedSize(25, 25)
        close_button.clicked.connect(self.handleCloseButton)

        title_layout.addStretch(1)
        title_layout.addWidget(title_label)
        title_layout.addStretch(1)
        title_layout.addWidget(close_button, alignment=Qt.AlignRight)

        self.main_layout.addLayout(title_layout)
        self.setCentralWidget(self.main_widget)

    def setWindowPosition(self):
        """
        Set the window position to the center of the screen.
        """
        screen_geometry = QApplication.desktop().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def handleCloseButton(self):
        """
        Close the window.
        """
        self.close()

    def mousePressEvent(self, event):
        """
        Allow the window to be moved by clicking and dragging anywhere on the window.
        """
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.start_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """
        Move the window when dragging.
        """
        if Qt.LeftButton and self.is_dragging:
            self.move(event.globalPos() - self.start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """
        Stop dragging the window.
        """
        self.is_dragging = False

    def paintEvent(self, event):
        """
        Create a rounded rectangle with a semi-transparent white background.
        """
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 20, 20)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

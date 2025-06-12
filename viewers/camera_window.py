import sys
import config
from camera_widget import CameraGridWidget
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QSizePolicy
from PySide6.QtGui import QGuiApplication, QImage, QPixmap
from PySide6.QtCore import Qt, QSize, Signal
import cv2

from RTSPCamera import RTSPCamera

class SingleCameraWidget(QWidget):
    clicked = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)

        self.label = QLabel("No Video")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setStyleSheet("background-color: black; color: white;")
        self.label.setMinimumSize(0, 0)
        self.label.setText("Loading video...")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
    
    def set_camera(self, camera: RTSPCamera):
        self.camera = camera
        self.camera.frame_received.connect(self.update_frame)
        self.camera.start()
    
    def stop_camera(self):
        self.camera.stop()
        self.camera = None

    def sizeHint(self):
        return QSize(320, 240)

    def minimumSizeHint(self):
        return QSize(0, 0)

    def update_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(img)
        self.label.setPixmap(pix.scaled(
            self.label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

    def stop_camera(self):
        self.camera.stop()

    def mousePressEvent(self, event):
        self.clicked.emit("clicked")
        super().mousePressEvent(event)

class CameraWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera View")

        # Load config and build camera grid (cols/rows are read inside)
        cfg = config.load()
        self.camera_grid = CameraGridWidget(cfg)
        self.setLayout(self.camera_grid.stack)

        # Query available screen geometry (so we never exceed it)
        screen_geom = QGuiApplication.primaryScreen().availableGeometry()
        max_w, max_h = screen_geom.width(), screen_geom.height()

        # Pick a “reasonable default” that’s <= (max_w, max_h):
        desired_w, desired_h = 1200, 800
        final_w = min(desired_w, max_w)
        final_h = min(desired_h, max_h)
        self.resize(final_w, final_h)

    def closeEvent(self, event):
        self.camera_grid.stop_cameras()
        event.accept()
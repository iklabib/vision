from PySide6.QtWidgets import (
    QWidget, QLabel, QStackedLayout,
    QGridLayout, QSizePolicy, QVBoxLayout
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QTimer
from RTSPCamera import RTSPCamera
from config import Config
import cv2
import math

class CameraWidget(QLabel):
    clicked = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Allow this label to shrink down to zero if needed:
        self.setMinimumSize(0, 0)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background-color: black; color: white;")
        self.setText("No Video")
        self._ideal = QSize(320, 240)
    
    def sizeHint(self):
        return self._ideal
    
    def minimumSizeHint(self):
        # If you truly want to allow even smaller, return QSize(0,0):
        return QSize(0, 0)

    def update_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(img)
        self.setPixmap(pix.scaled(self.size(),
                                  Qt.KeepAspectRatio,
                                  Qt.SmoothTransformation))

    def mousePressEvent(self, event):
        self.clicked.emit(self)


class CameraGridWidget(QWidget):
    clicked = Signal(str)
    def __init__(self, configs: Config):
        super().__init__()

        self.current_ip = None

        self.page = 0
        self.configs = configs
        self.cameras = []
        self.widgets = []

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next)
        self.timer.start(600000)  # 10 minutes in milliseconds

        self.stack = QStackedLayout(self)
        self.cols = configs.grid.column
        self.rows = configs.grid.row

        self.grid_page = QWidget()
        self.grid_l = QGridLayout()
        self.grid_l.setContentsMargins(0, 0, 0, 0)
        self.grid_l.setSpacing(0)

        hbox = QVBoxLayout()
        hbox.addLayout(self.grid_l)
        self.grid_page.setLayout(hbox)

        self.stack.addWidget(self.grid_page)

        self.full_page = QWidget()
        self.full_layout = QVBoxLayout(self.full_page)
        self.full_layout.setContentsMargins(0, 0, 0, 0)
        self.stack.addWidget(self.full_page)
    
    def next(self):
        max_cells = self.cols * self.rows
        max_page = math.ceil(len(self.configs.cameras) / max_cells)

        if self.page < max_page:
            self.page += 1
        else:
            self.page = 1  # Reset to the first page after cycling through all

        self.move_to(self.page)

    def prev(self):
        if self.page > 1:
            self.page -= 1
        self.move_to(self.page)
    
    def move_by_ip(self, ip):
        if self.current_ip == ip:
            return

        self.current_ip = ip

        page = 0
        for camera in self.configs.cameras:
            page += 1
            if camera.host == ip:
                break
        else:
            return
        
        self.move_to(page)
    
    def get_camera_by_host(self, host: str) -> RTSPCamera | None:
        self.cameras: list[RTSPCamera]
        for cam in self.cameras:
            if cam.host == host:
                return cam
        return None

    def move_to(self, page: int):
        max_cells = self.cols * self.rows
        start = (page - 1) * max_cells
        cameras = self.configs.cameras[start:start + max_cells]

        for widget in self.widgets:
            self.grid_l.removeWidget(widget)
            widget.setParent(None)

        self.widgets.clear()
        self.cameras.clear()

        for idx in range(len(cameras)):
            r, c = divmod(idx, self.cols)
            w = CameraWidget()
            self.grid_l.addWidget(w, r, c)
            self.widgets.append(w)

            info = cameras[idx]
            cam = RTSPCamera(info.username, info.password, info.host, info.port)
            cam.frame_received.connect(w.update_frame)
            cam.start()

            self.cameras.append(cam)
        
    def stop_cameras(self):
        for cam in self.cameras:
            cam.stop()
        self.cameras = []
    
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit(self.current_ip) 

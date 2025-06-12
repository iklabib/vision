import time
import av
import av.container
import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QMessageBox


class RTSPCamera(QThread):
    frame_received = Signal(np.ndarray)

    def __init__(self, username, password, host, port=554, parent=None):
        super().__init__(parent)
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.running = False
        self.rtsp_url = f"rtsp://{username}:{password}@{host}:{port}/"

    def run(self):
        self.running = True
        container: av.container.InputContainer | None = None
        while self.running:
            try:
                # Open the RTSP stream
                options = {
                    'rtsp_transport': 'tcp',  # use TCP instead of UDP (less packet loss)
                    'buffer_size': '10000000',  # increase buffer size (in bytes)
                    'max_delay': '500000',      # max delay in microseconds
                    'fflags': 'nobuffer',       # reduce latency by not buffering much
                }
                container = av.open(self.rtsp_url, options=options, timeout=5)  # open with timeout

                stream = next(s for s in container.streams if s.type == 'video')

                for packet in container.demux(stream):
                    if not self.running:
                        break
                    for frame in packet.decode():
                        if not self.running:
                            break
                        img = frame.to_ndarray(format='bgr24')  # get numpy BGR frame like OpenCV
                        self.frame_received.emit(img)
                        time.sleep(0.004)  # simulate video frame rate

            except av.error.FFmpegError as e:
                # msg = f"Error opening stream {self.rtsp_url}: {e}"
                # QMessageBox.warning(None, "Error opening stream", msg)
                self.retry_stream()

            except av.error.ConnectionResetError:
                # If connection reset, try reconnecting after a short delay
                # msg = f"Error opening stream {self.rtsp_url}: {e}"
                # QMessageBox.warning(None, "Error opening stream", msg)
                self.retry_stream()

            finally:
                if container:
                    container.close()

    def retry_stream(self):
        """Handle reconnection attempts after a failure."""
        retry_delay = 5  # seconds to wait before retrying
        for _ in range(5):  # Try 5 times before giving up
            if not self.running:
                return
            time.sleep(retry_delay)
            print(f"Retrying to connect to {self.rtsp_url}...")
            try:
                # Try to reconnect
                options = {
                    'rtsp_transport': 'tcp',
                    'buffer_size': '10000000',
                    'max_delay': '500000',
                    'fflags': 'nobuffer',
                }
                container = av.open(self.rtsp_url, options=options, timeout=5)  # open with timeout
                if container:
                    print(f"Reconnected to {self.rtsp_url}")
                    return  # Successfully reconnected, exit retry loop
            except av.error.ConnectionResetError:
                continue

        # If still failed after retries, display a message and stop
        QMessageBox.warning(None, "Stream Reconnection Failed", f"Unable to reconnect to {self.rtsp_url}.")

    def stop(self):
        """Stop the camera streaming."""
        self.running = False
        self.wait()  # Wait for the thread to finish before returning

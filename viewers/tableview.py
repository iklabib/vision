import sys
import json
import psycopg2
from RTSPCamera import RTSPCamera
import config
import connection
from camera_window import CameraGridWidget, SingleCameraWidget
from datetime import datetime, timedelta
from hikvision_events import hikvision_event_stream
from PySide6.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QHBoxLayout, QWidget, QHeaderView, QStackedLayout
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QThread, Signal, QTimer


class PgTableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self._data = data
        self._headers = headers

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            return str(self._data[index.row()][index.column()])
        elif role == Qt.TextAlignmentRole:
            # Center-align date_time column (index 3)
            if index.column() == 3:
                return Qt.AlignCenter
            else:
                return Qt.AlignLeft | Qt.AlignVCenter
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def update_row(self, ip, timestamp, count):
        """Update the row for the given IP with the new timestamp and count"""
        for i, row in enumerate(self._data):
            if row[0] == ip:
                # Convert the tuple to a list so that we can modify it
                updated_row = list(row)
                updated_row[3] = timestamp  # Update timestamp
                updated_row[2] = count  # Update count
                # Convert it back to a tuple and update the row
                self._data[i] = tuple(updated_row)
                self.dataChanged.emit(self.index(i, 0), self.index(i, self.columnCount() - 1))
                break


class EventListenerThread(QThread):
    new_event = Signal(list)  # emits new row data as list

    def __init__(self, ip_events, reset_time_minutes):
        super().__init__()
        self.ip_events = ip_events
        self.reset_time_minutes = reset_time_minutes
        self.timer = QTimer()
        self.timer.timeout.connect(self.reset_inactive_counters)
        self.timer.start(60 * 1000)  # Check every minute

    def run(self):
        # Listen indefinitely on the event stream
        for event_data in hikvision_event_stream():
            try:
                payload = json.loads(event_data['payload'])
                ip = payload.get('ip_address')
                event_time = datetime.fromisoformat(payload.get('date_time'))

                # Update the event counter and timestamp
                if ip not in self.ip_events:
                    self.ip_events[ip] = {
                        'last_event': event_time,
                        'count': 1
                    }
                else:
                    last_event = self.ip_events[ip]['last_event']
                    if event_time - last_event > timedelta(minutes=self.reset_time_minutes):
                        self.ip_events[ip]['count'] = 1  # Reset count if time difference is more than N minutes
                    else:
                        self.ip_events[ip]['count'] += 1  # Increment count
                    self.ip_events[ip]['last_event'] = event_time

                row = [
                    ip,
                    payload.get('channel_name'),
                    self.ip_events[ip]['count'],
                    event_time.strftime("%d-%m-%Y %H:%M:%S"),
                ]
                self.new_event.emit(row)
            except Exception as e:
                print(f"Error processing event: {e}")

    def reset_inactive_counters(self):
        """Reset counters for IPs that have been inactive for too long."""
        now = datetime.now()
        for ip, event_data in list(self.ip_events.items()):
            event_naive = event_data['last_event'].replace(tzinfo=None)
            if now - event_naive > timedelta(minutes=self.reset_time_minutes):
                event_data['count'] = 0 


class PgTableView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Event Notifications and Camera View")
        self.resize(1200, 800)

        # Main layout with two sections: event table on the left, cameras on the right
        main_layout = QHBoxLayout()

        # --- Left Section: Event Table ---
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)

        layout = QVBoxLayout()
        layout.addWidget(self.table_view)

        container = QWidget()
        container.setLayout(layout)

        # --- Right Section: Camera Grid ---
        cfg = config.load()

        self.camera_grid = CameraGridWidget(cfg)
        self.camera_grid.next()
        self.camera_grid.clicked.connect(self.fullscreen_window)

        self.single_camera = SingleCameraWidget()
        self.single_camera.clicked.connect(self.exit_fullscreen)

        main_widget = QWidget()
        main_layout.addWidget(self.camera_grid, 2)
        main_layout.addWidget(container, 3)
        main_widget.setLayout(main_layout)

        self.vstack = QStackedLayout()
        self.vstack.addWidget(main_widget)
        self.vstack.addWidget(self.single_camera)

        # Initialize the model for the event table
        self.model = None
        self.load_data()

        # Enable sorting for the event table
        self.table_view.setSortingEnabled(True)

        # Event listener thread for new events
        self.ip_events = {}
        self.listener_thread = EventListenerThread(self.ip_events, 5)
        self.listener_thread.new_event.connect(self.update_row)
        self.listener_thread.start()

        # Set the layout for the main window
        container = QWidget()
        container.setLayout(self.vstack)
        self.setCentralWidget(container)

        self.full_screen_widget = None

        self.vstack.setCurrentIndex(0)
    
    def exit_fullscreen(self):
        self.vstack.setCurrentIndex(0)
        self.single_camera.stop_camera()

    def load_data(self):
        conf = connection.load('cctv')
        conn = psycopg2.connect(
            host=conf.host,
            port=conf.port,
            database=conf.database,
            user=conf.username,
            password=conf.password
        )
        cursor = conn.cursor()

        query = """
        WITH RankedEvents AS (
            SELECT 
                ip_address, 
                channel_name, 
                0 as counter, 
                date_time,
                ROW_NUMBER() OVER (PARTITION BY ip_address ORDER BY date_time DESC) AS rn
            FROM event_notifications
        )
        SELECT 
            ip_address, 
            channel_name, 
            0 as counter, 
            TO_CHAR(date_time, 'DD-MM-YYYY HH24:MI:SS') AS date_time
        FROM RankedEvents
        WHERE rn = 1
        ORDER BY date_time DESC;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        headers = ["IP Address", "Channel Name", "Event Count", "Date Time"]
        self.model = PgTableModel(rows, headers)
        self.table_view.setModel(self.model)
        self.table_view.resizeColumnsToContents()
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.table_view.clicked.connect(self.change_camera_view)

    def update_row(self, row):
        ip = row[0]
        if self.model is not None:
            self.model.update_row(ip, row[3], row[2])
    
    def change_camera_view(self, index):
        if not index.isValid():
            return

        row = index.row()
        model = self.table_view.model()

        row_data = [
            model.data(model.index(row, col), Qt.DisplayRole)
            for col in range(model.columnCount())
        ]
        ip, channel, count, datetime = row_data

        self.camera_grid.move_by_ip(ip)

    def fullscreen_window(self, ip):
        print(ip)
        # if not index.isValid():
        #     return
        
        # row = index.row()
        # model = self.table_view.model()

        # row_data = [
        #     model.data(model.index(row, col), Qt.DisplayRole)
        #     for col in range(model.columnCount())
        # ]

        # ip, channel, count, datetime = row_data
        cam = self.camera_grid.get_camera_by_host(ip)
        if not cam:
            entry = config.get_entry_by_host(ip)
            # TODO: handle this
            if not entry:
                return

            cam = RTSPCamera(entry.username, entry.password, entry.host, entry.port)

        self.single_camera.set_camera(cam)
        self.vstack.setCurrentIndex(1)

    def closeEvent(self, event):
        # Handle closing event to stop all cameras
        self.camera_grid.stop_cameras()
        if self.full_screen_widget:
            self.full_screen_widget.stop_camera()
        event.accept()
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PgTableView()
    window.showMaximized()
    sys.exit(app.exec())

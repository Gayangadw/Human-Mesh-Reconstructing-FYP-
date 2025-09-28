import sys
import os
import webbrowser
import shutil
import tempfile
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton,
    QFileDialog, QVBoxLayout, QLabel, QTextEdit, QHBoxLayout
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QColor
import open3d as o3d


class MeshGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)  # Frameless window
        self.setGeometry(100, 100, 1000, 700)

        # Track mouse position for dragging the window
        self.old_pos = None

        # Central Widget
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color: #2E3440;")
        self.setCentralWidget(self.central_widget)

        # Main layout
        self.layout = QVBoxLayout()
        self.layout.setSpacing(15)
        self.central_widget.setLayout(self.layout)

        # Custom title bar
        self.title_bar = QWidget()
        self.title_bar.setStyleSheet("background-color: #4C566A;")
        self.title_layout = QHBoxLayout()
        self.title_layout.setContentsMargins(0, 0, 0, 0)
        self.title_bar.setLayout(self.title_layout)

        # Title label centered
        self.title_label = QLabel("Mesh Reconstructing")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.title_label.setStyleSheet("color: white; padding: 10px;")
        self.title_layout.addWidget(self.title_label)

        # Close button
        self.close_button = QPushButton("X")
        self.close_button.setFixedSize(40, 30)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #BF616A; 
                color: white; 
                font-weight: bold; 
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #D08770;
            }
        """)
        self.close_button.clicked.connect(self.close)
        self.title_layout.addWidget(self.close_button)

        self.layout.addWidget(self.title_bar)

        # Button styling
        button_style = """
            QPushButton {
                background-color: #5E81AC;
                color: white;
                font-size: 16px;
                padding: 10px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
        """

        # Load mesh button
        self.load_button = QPushButton("Load Mesh (.obj/.fbx)")
        self.load_button.setStyleSheet(button_style)
        self.load_button.clicked.connect(self.load_mesh)
        self.layout.addWidget(self.load_button)

        # Rig in Mixamo
        self.rig_button = QPushButton("Rig in Mixamo")
        self.rig_button.setStyleSheet(button_style)
        self.rig_button.clicked.connect(self.open_mixamo)
        self.layout.addWidget(self.rig_button)

        # Import rigged FBX to Unity
        self.import_button = QPushButton("Import Rigged FBX to Unity")
        self.import_button.setStyleSheet(button_style)
        self.import_button.clicked.connect(self.import_to_unity)
        self.layout.addWidget(self.import_button)

        # Status log
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setStyleSheet(
            "background-color: #3B4252; color: #ECEFF4; font-size: 14px; border-radius: 5px; padding: 5px;"
        )
        self.layout.addWidget(self.status_log)

        # Mesh holder
        self.mesh = None
        self.mesh_file = None

    # Make frameless window draggable
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def log(self, message):
        self.status_log.append(message)
        print(message)

    # Load OBJ or FBX
    def load_mesh(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Mesh", "", "Mesh Files (*.obj *.fbx)"
        )
        if file_name:
            self.mesh_file = file_name
            try:
                self.mesh = o3d.io.read_triangle_mesh(file_name)
                if self.mesh.has_textures():
                    self.log(f"Loaded mesh with textures: {file_name}")
                else:
                    self.log(f"Loaded mesh without textures: {file_name}")

                # Open3D visualizer in non-blocking mode
                self.visualize_mesh(self.mesh)

            except Exception as e:
                self.log(f"Error loading mesh: {str(e)}")

    def visualize_mesh(self, mesh):
        tmp_dir = tempfile.gettempdir()
        tmp_file = os.path.join(tmp_dir, "tmp_mesh.ply")
        o3d.io.write_triangle_mesh(tmp_file, mesh)
        mesh_tmp = o3d.io.read_triangle_mesh(tmp_file)
        o3d.visualization.draw_geometries([mesh_tmp])

    # Open Mixamo website
    def open_mixamo(self):
        webbrowser.open("https://www.mixamo.com")
        self.log(
            "Opened Mixamo in your default browser. Upload your mesh and download rigged FBX.")

    # Copy downloaded FBX to Unity Assets
    def import_to_unity(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Rigged FBX", "", "FBX Files (*.fbx)"
        )
        if file_name:
            try:
                unity_assets_path = QFileDialog.getExistingDirectory(
                    self, "Select Unity Assets Folder"
                )
                if unity_assets_path:
                    base_name = os.path.basename(file_name)
                    target_path = os.path.join(unity_assets_path, base_name)
                    os.makedirs(unity_assets_path, exist_ok=True)
                    shutil.copy(file_name, target_path)
                    self.log(
                        f"Copied rigged FBX to Unity Assets: {target_path}")
            except Exception as e:
                self.log(f"Error copying FBX: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MeshGUI()
    window.show()
    sys.exit(app.exec_())

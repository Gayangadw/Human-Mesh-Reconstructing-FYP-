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
import numpy as np


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
        self.title_label = QLabel("OBJ Mesh Viewer")
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

        # Load OBJ button
        self.load_button = QPushButton("Load OBJ File")
        self.load_button.setStyleSheet(button_style)
        self.load_button.clicked.connect(self.load_obj_mesh)
        self.layout.addWidget(self.load_button)

        # Rig in Mixamo
        self.rig_button = QPushButton("Rig in Mixamo")
        self.rig_button.setStyleSheet(button_style)
        self.rig_button.clicked.connect(self.open_mixamo)
        self.layout.addWidget(self.rig_button)

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

    def find_texture_file(self, obj_dir, texture_ref):
        """Find texture file with various extensions and paths"""
        # Try different locations and extensions
        possible_paths = [
            os.path.join(obj_dir, texture_ref),
            os.path.join(obj_dir, os.path.basename(texture_ref)),
        ]

        # Try different extensions
        base_name = os.path.splitext(texture_ref)[0]
        extensions = ['.jpg', '.jpeg', '.png',
                      '.bmp', '.tga', '.JPG', '.JPEG', '.PNG']
        for ext in extensions:
            possible_paths.append(os.path.join(obj_dir, base_name + ext))

        for test_path in possible_paths:
            if os.path.exists(test_path):
                return test_path
        return None

    def load_obj_with_textures(self, obj_path):
        """Enhanced OBJ loading with texture support"""
        self.log(f"Loading OBJ file: {obj_path}")

        if not os.path.exists(obj_path):
            raise FileNotFoundError(f"OBJ file not found: {obj_path}")

        # Get directory of OBJ file
        obj_dir = os.path.dirname(obj_path)

        # Step 1: Analyze OBJ file for materials and texture coordinates
        mtl_files = []
        has_texture_coords = False

        try:
            with open(obj_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('mtllib'):
                        mtl_file = line.split(' ', 1)[1]
                        mtl_files.append(mtl_file)
                        self.log(f"Found material library: {mtl_file}")
                    elif line.startswith('vt'):
                        has_texture_coords = True
        except Exception as e:
            self.log(f"Warning: Could not analyze OBJ file structure: {e}")

        # Step 2: Load MTL files and find textures
        texture_paths = []
        if mtl_files:
            for mtl_file in mtl_files:
                mtl_path = os.path.join(obj_dir, mtl_file)
                if os.path.exists(mtl_path):
                    try:
                        with open(mtl_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line in f:
                                line = line.strip()
                                if line.startswith('map_Kd'):  # Diffuse texture map
                                    texture_file = line.split(' ', 1)[1]
                                    texture_paths.append(texture_file)
                                    self.log(
                                        f"Found texture reference: {texture_file}")
                    except Exception as e:
                        self.log(f"Warning: Could not read MTL file: {e}")

        # Step 3: Load the mesh
        self.log("Loading 3D mesh...")
        mesh = o3d.io.read_triangle_mesh(obj_path, enable_post_processing=True)
        mesh.compute_vertex_normals()

        self.log(
            f"Mesh loaded - Vertices: {len(mesh.vertices):,}, Triangles: {len(mesh.triangles):,}")

        # Step 4: Handle textures
        if len(mesh.textures) == 0 and texture_paths:
            self.log("Textures not auto-loaded, attempting manual loading...")
            for texture_ref in texture_paths:
                found_texture = self.find_texture_file(obj_dir, texture_ref)
                if found_texture:
                    try:
                        texture = o3d.io.read_image(found_texture)
                        mesh.textures = [texture]
                        self.log(
                            f"✅ Successfully loaded texture: {os.path.basename(found_texture)}")
                        break
                    except Exception as e:
                        self.log(
                            f"❌ Error loading texture {found_texture}: {e}")
                else:
                    self.log(f"❌ Texture file not found: {texture_ref}")

        # Step 5: Final texture status
        if len(mesh.textures) > 0:
            self.log("✅ Mesh ready with textures!")
        else:
            self.log("⚠️ No textures available, using colored mesh")
            # Apply a default color
            mesh.paint_uniform_color([0.7, 0.5, 0.3])  # Skin tone

        return mesh

    def load_obj_mesh(self):
        """Load and visualize OBJ file with textures"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open OBJ File", "", "OBJ Files (*.obj)"
        )

        if file_name:
            self.mesh_file = file_name
            try:
                # Use enhanced OBJ loader
                self.mesh = self.load_obj_with_textures(file_name)

                # Visualize the mesh
                self.visualize_mesh(self.mesh)

            except Exception as e:
                self.log(f"❌ Error loading OBJ file: {str(e)}")

    def visualize_mesh(self, mesh):
        """Visualize mesh with proper texture handling"""
        try:
            self.log("Opening 3D viewer...")

            # Visualization options for better rendering
            vis = o3d.visualization.Visualizer()
            vis.create_window(window_name="OBJ Mesh Viewer",
                              width=1200, height=800)

            # Add the mesh to visualizer
            vis.add_geometry(mesh)

            # Set up camera and lighting for better visualization
            vis.get_render_option().mesh_show_back_face = False
            vis.get_render_option().mesh_show_wireframe = False
            vis.get_render_option().light_on = True

            # Run visualization
            vis.run()
            vis.destroy_window()

            self.log("3D viewer closed")

        except Exception as e:
            self.log(f"❌ Error in visualization: {str(e)}")

    # Open Mixamo website
    def open_mixamo(self):
        webbrowser.open("https://www.mixamo.com")
        self.log(
            "Opened Mixamo in your default browser. Upload your OBJ mesh and download rigged FBX.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MeshGUI()
    window.show()
    sys.exit(app.exec_())

import open3d as o3d
import os
import numpy as np


def comprehensive_mesh_analysis_and_load(obj_path):
    """Comprehensive analysis and loading of 3D mesh with textures"""

    print("=== 3D Mesh Analysis and Loading ===")
    print(f"OBJ file: {obj_path}")

    # Get directory of OBJ file
    obj_dir = os.path.dirname(obj_path)

    # 1. Analyze OBJ file structure
    print("\n1. Analyzing OBJ file structure...")
    has_mtl = False
    has_texture_coords = False
    mtl_files = []

    try:
        with open(obj_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith('mtllib'):
                    has_mtl = True
                    mtl_file = line.split(' ', 1)[1]
                    mtl_files.append(mtl_file)
                    print(f"   Found material library: {mtl_file}")
                elif line.startswith('vt'):
                    has_texture_coords = True
    except Exception as e:
        print(f"   Error reading OBJ file: {e}")

    print(f"   Has material library: {has_mtl}")
    print(f"   Has texture coordinates: {has_texture_coords}")

    # 2. Analyze MTL file if it exists
    texture_files = []
    if has_mtl and mtl_files:
        print("\n2. Analyzing MTL files...")
        for mtl_file in mtl_files:
            mtl_path = os.path.join(obj_dir, mtl_file)
            if os.path.exists(mtl_path):
                print(f"   Reading: {mtl_path}")
                try:
                    with open(mtl_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith('map_Kd'):
                                texture_file = line.split(' ', 1)[1]
                                texture_files.append(texture_file)
                                print(f"   Found texture: {texture_file}")
                except Exception as e:
                    print(f"   Error reading MTL file: {e}")
            else:
                print(f"   MTL file not found: {mtl_path}")

    # 3. Find and verify texture files
    found_texture_path = None
    if texture_files:
        print("\n3. Searching for texture files...")
        for texture_file in texture_files:
            # Try different locations and extensions
            possible_paths = [
                os.path.join(obj_dir, texture_file),
                os.path.join(obj_dir, os.path.basename(texture_file)),
            ]

            # Try different extensions
            base_name = os.path.splitext(texture_file)[0]
            extensions = ['.jpg', '.jpeg', '.png',
                          '.bmp', '.tga', '.JPG', '.JPEG', '.PNG']
            for ext in extensions:
                possible_paths.append(os.path.join(obj_dir, base_name + ext))

            for test_path in possible_paths:
                if os.path.exists(test_path):
                    found_texture_path = test_path
                    print(f"   ✅ Found texture: {test_path}")
                    break
                else:
                    print(f"   ❌ Not found: {test_path}")

            if found_texture_path:
                break

    # 4. Load the mesh
    print("\n4. Loading mesh...")
    mesh = o3d.io.read_triangle_mesh(obj_path, enable_post_processing=True)
    mesh.compute_vertex_normals()

    # Display mesh info
    print(f"   Vertices: {len(mesh.vertices):,}")
    print(f"   Triangles: {len(mesh.triangles):,}")
    print(f"   Textures auto-loaded: {len(mesh.textures)}")

    # 5. Manual texture loading if needed
    if len(mesh.textures) == 0 and found_texture_path:
        print("\n5. Loading texture manually...")
        try:
            texture = o3d.io.read_image(found_texture_path)
            mesh.textures = [texture]
            print(f"   ✅ Manual texture loaded successfully!")
        except Exception as e:
            print(f"   ❌ Error loading texture: {e}")

    # 6. Final status and visualization
    print("\n6. Final Status:")
    if len(mesh.textures) > 0:
        print("   ✅ Ready to visualize with textures!")
        show_textured = True
    else:
        print("   ⚠️  No textures available. Will use colored mesh.")
        show_textured = False

    # 7. Visualize the mesh
    print("\n7. Visualization...")
    if show_textured:
        print("   Displaying textured mesh")
        o3d.visualization.draw_geometries([mesh],
                                          mesh_show_wireframe=False,
                                          mesh_show_back_face=False,
                                          window_name="3D Mesh with Textures")
    else:
        print("   Displaying colored mesh")
        # Create a colored mesh
        colored_mesh = o3d.geometry.TriangleMesh()
        colored_mesh.vertices = mesh.vertices
        colored_mesh.triangles = mesh.triangles
        colored_mesh.vertex_normals = mesh.vertex_normals
        colored_mesh.paint_uniform_color([0.7, 0.5, 0.3])  # Skin tone

        o3d.visualization.draw_geometries([colored_mesh],
                                          mesh_show_wireframe=False,
                                          mesh_show_back_face=False,
                                          window_name="3D Mesh (Colored)")

    return mesh


# ===================== MAIN EXECUTION =====================
if __name__ == "__main__":
    # Path to your OBJ file
    path = r"C:\Users\User\Downloads\97-free_091_aya_obj\091_W_Aya_100K.obj"

    # Run comprehensive analysis and loading
    mesh = comprehensive_mesh_analysis_and_load(path)

    print("\n=== Analysis Complete ===")

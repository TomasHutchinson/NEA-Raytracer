import numpy as np
import os
import random
import primitives
from transform import transform as trans
from material import Material

class mesh:
    def __init__(self, filepath=""):
        self.triangles = []
        self.aabb = []
        self.materials = []
        self.transform = trans()
        if filepath:
            self.load(filepath)

    def intersect(self, ro: np.ndarray, rd: np.ndarray):
        inv_matrix = np.linalg.inv(self.transform.get_transformation_matrix())
        ro_local = (inv_matrix @ np.append(ro, 1.0))[:3]
        rd_local = (inv_matrix @ np.append(rd, 0.0))[:3]

        if not self._intersects_aabb(ro_local, rd_local):
            return np.full(3, 1e10), np.zeros(3), np.zeros(2), np.zeros(3)

        intersections = []
        for tri in self.triangles:
            hit = tri.intersect(ro_local, rd_local)
            if hit is not None:
                intersections.append((*hit, tri))

        if not intersections:
            return np.full(3, 1e10), np.zeros(3), np.zeros(2), np.zeros(3)

        # closest hit
        intersections.sort(key=lambda x: np.linalg.norm(x[0] - ro_local))
        hit_point_local, normal_local, tri = intersections[0][:3]

        M = self.transform.get_transformation_matrix()
        hit_point_world = (M @ np.append(hit_point_local, 1.0))[:3]
        normal_world = (M @ np.append(normal_local, 0.0))[:3]
        normal_world /= np.linalg.norm(normal_world) + 1e-8

        uv = tri.uv(hit_point_local)
        color = tri.color(uv)
        return hit_point_world, normal_world, uv, color

    def _intersects_aabb(self, ro, rd):
        inv_dir = 1.0 / (rd + 1e-12)
        tmin = (self.aabb[0] - ro) * inv_dir
        tmax = (self.aabb[1] - ro) * inv_dir
        t1 = np.minimum(tmin, tmax)
        t2 = np.maximum(tmin, tmax)
        t_near = np.max(t1)
        t_far = np.min(t2)
        return t_far >= t_near and t_far >= 0

    def load(self, filepath):
        vertices, normals, uvs = [], [], []
        faces = []
        current_mtl = None
        materials = {}

        with open(filepath, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if line.startswith("mtllib "):
                    mtl_file = line.split()[1]
                    if mtl_file.startswith("./"): mtl_file = mtl_file[2:]
                    mtl_path = os.path.join(os.path.dirname(filepath), mtl_file)
                    if os.path.isfile(mtl_path):
                        materials.update(self.load_mtl(mtl_path))
                    else:
                        print(f"Warning: MTL file '{mtl_file}' not found. Skipping.")

                elif line.startswith("usemtl "):
                    current_mtl = line.split()[1]

                elif line.startswith("v "):
                    vertices.append(np.array(list(map(float, line.split()[1:4])), dtype=np.float32))

                elif line.startswith("vn "):
                    n = np.array(list(map(float, line.split()[1:4])), dtype=np.float32)
                    n /= np.linalg.norm(n) + 1e-8
                    normals.append(n)

                elif line.startswith("vt "):
                    uvs.append(np.array(list(map(float, line.split()[1:3])), dtype=np.float32))

                elif line.startswith("f "):
                    face = []
                    for part in line.split()[1:]:
                        vals = part.split('/')
                        v_idx = int(vals[0]) - 1 if vals[0] else None
                        vt_idx = int(vals[1]) - 1 if len(vals) > 1 and vals[1] else None
                        vn_idx = int(vals[2]) - 1 if len(vals) > 2 and vals[2] else None
                        face.append((v_idx, vt_idx, vn_idx))
                    faces.append((face, current_mtl))

        # Triangulate faces
        tris = []
        # create one default material to reuse
        default_material = Material()

        for face, matname in faces:
            if len(face) < 3:
                continue

            # gather per-corner attributes
            tri_positions = [vertices[v_idx] for v_idx, _, _ in face]
            tri_normals = [normals[vn_idx] if vn_idx is not None else None for _, _, vn_idx in face]
            tri_uvs = [uvs[vt_idx] if vt_idx is not None else np.zeros(2, dtype=np.float32)
                    for _, vt_idx, _ in face]

            # fan-triangulate the polygon
            v0 = 0
            for i in range(1, len(tri_positions) - 1):
                i1, i2 = i, i + 1
                tri = primitives.Triangle((tri_positions[v0],
                                        tri_positions[i1],
                                        tri_positions[i2]))

                # normals: only assign if all three corners have normals
                if all(n is not None for n in tri_normals):
                    tri.normals = np.array([tri_normals[v0],
                                            tri_normals[i1],
                                            tri_normals[i2]], dtype=np.float32)
                else:
                    # leave as [] so your existing fallback logic can run
                    tri.normals = []

                # UVs (always assign a 3x2 float32 array)
                tri.uvs = np.array([tri_uvs[v0],
                                    tri_uvs[i1],
                                    tri_uvs[i2]], dtype=np.float32)

                # MATERIAL ASSIGNMENT (use matname from faces tuple)
                if matname is not None:
                    mat = materials.get(matname)
                    if mat is None:
                        # debug output to help find missing/typo'd material names
                        print(f"Warning: material '{matname}' not found in MTLs. Using default material.")
                        tri.material = default_material
                    else:
                        tri.material = mat
                else:
                    tri.material = default_material

                tris.append(tri)

        self.triangles = tris
        self.materials = list(materials.values())
        all_vertices_np = np.array(vertices, dtype=np.float32)
        self.aabb = (np.min(all_vertices_np, axis=0), np.max(all_vertices_np, axis=0))

    def load_mtl(self, mtl_path: str) -> dict:
        materials = {}
        if not os.path.isfile(mtl_path):
            print(f"Warning: MTL file '{mtl_path}' does not exist.")
            return materials

        current = None
        with open(mtl_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith("newmtl "):
                    name = line.split()[1]
                    current = Material(name)
                    materials[name] = current
                elif line.startswith("Kd ") and current:
                    _, r, g, b = line.split()
                    current.albedo = np.array([float(r), float(g), float(b)], dtype=np.float32)
                elif line.startswith("map_Kd ") and current:
                    tex_path = line.split()[1]
                    tex_full = os.path.join(os.path.dirname(mtl_path), tex_path)
                    current.load_texture(tex_full)
        return materials

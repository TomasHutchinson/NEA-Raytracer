import numpy as np
import random

import primitives
from transform import transform as trans

class mesh:
    triangles = []
    aabb = []

    transform = trans()

    def __init__(self, filepath = ""):
        print("init")
        if filepath != "":
            self.load(filepath)

    def intersect(self, ro: np.ndarray, rd: np.ndarray) -> tuple: #(hit_point_world: np.ndarray, normal_world: np.ndarray, uv: np.ndarray, color: np.ndarray)
        # Transform ray to local space
        inv_matrix = np.linalg.inv(self.transform.get_transformation_matrix())

        # Convert ray origin and direction to homogeneous coordinates
        ro_h = np.append(ro, 1.0)
        rd_h = np.append(rd, 0.0)  # Directions use 0 in homogeneous coords

        ro_local = (inv_matrix @ ro_h)[:3]
        rd_local = (inv_matrix @ rd_h)[:3]

        if not self._intersects_aabb(ro_local, rd_local):
            return (np.array([1e10, 1e10, 1e10]), np.array([0, 0, 0]), np.array([0.0, 0.0]), np.array([0.0, 0.0, 0.0]))  # Misses AABB

        intersections = []
        for tri in self.triangles:
            hit = tri.intersect(ro_local, rd_local)
            if hit is not None:
                hit_point_local, normal_local = hit
                intersections.append((hit_point_local, normal_local, tri))

        if intersections:
            # Return closest intersection
            intersections.sort(key=lambda x: np.linalg.norm(x[0] - ro_local))
            hit_point_local, normal_local, tri = intersections[0]

            # Transform back to world space
            hit_point_world = self.transform.get_transformation_matrix() @ np.append(hit_point_local, 1.0)
            normal_world = self.transform.get_transformation_matrix() @ np.append(normal_local, 0.0)

            # Normalize normal 
            normal_world = normal_world[:3]
            normal_world /= np.linalg.norm(normal_world)

            # Get UV and color
            uv = tri.uv(hit_point_world)
            color = tri.color(uv)

            return (hit_point_world[:3], normal_world, uv, color)

        else:
            return (np.array([1e10, 1e10, 1e10]), np.array([0, 0, 0]), np.array([0.0, 0.0]), np.array([0.0, 0.0, 0.0]))  # No triangle hit
    
    def _intersects_aabb(self, ro: np.ndarray, rd: np.ndarray) -> bool:
        inv_dir = 1.0 / rd
        tmin = (self.aabb[0] - ro) * inv_dir
        tmax = (self.aabb[1] - ro) * inv_dir

        t1 = np.minimum(tmin, tmax)
        t2 = np.maximum(tmin, tmax)

        t_near = np.max(t1)
        t_far = np.min(t2)

        return t_far >= t_near and t_far >= 0

    def load(self, filepath):
        vertices = []
        normals = []
        faces = []

        with open(filepath, 'r') as file:
            for line in file:
                if line.startswith('v '):  # Vertex position
                    parts = line.strip().split()
                    vertex = list(map(float, parts[1:4]))
                    vertices.append(vertex)
                elif line.startswith('vn '):  # Vertex normal
                    parts = line.strip().split()
                    normal = list(map(float, parts[1:4]))
                    normals.append(normal)
                elif line.startswith('f '):  # Face
                    face = []
                    parts = line.strip().split()[1:]
                    for part in parts:
                        vals = part.split('//') if '//' in part else part.split('/')
                        v_idx = int(vals[0]) - 1
                        n_idx = int(vals[2]) - 1 if len(vals) > 2 and vals[2] else None
                        face.append((v_idx, n_idx))
                    faces.append(face)

        tris = []
        for face in faces:
            if len(face) != 3:
                continue  # Skip non-triangular faces or triangulate here if needed

            v0 = np.array(vertices[face[0][0]], dtype=np.float32)
            v1 = np.array(vertices[face[1][0]], dtype=np.float32)
            v2 = np.array(vertices[face[2][0]], dtype=np.float32)
            tri = primitives.Triangle((v0, v1, v2))
            tri.albedo = [random.uniform(0,1),random.uniform(0,1),random.uniform(0,1)]
            tris.append(tri)
        
        all_vertices_np = np.array(vertices)
        min_corner = np.min(all_vertices_np, axis=0)
        max_corner = np.max(all_vertices_np, axis=0)

        self.aabb = (min_corner, max_corner)
        self.triangles = tris
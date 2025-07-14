import numpy as np

import primitives

class mesh:
    triangles = []

    def __init__(self, filepath = ""):
        if filepath != "":
            self.load(filepath)

    def intersect(self, ro : np.ndarray, rd : np.ndarray) -> np.ndarray:
        intersections = []
        for tri in self.triangles:
            intersections.append(tri.intersect(ro, rd))
        return intersections[0]
    
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

        # Extract the vertices and normals from the face indices
        vertex_arrays = []
        normal_arrays = []

        for face in faces:
            v_arr = []
            n_arr = []
            for v_idx, n_idx in face:
                v_arr.append(vertices[v_idx])
                if n_idx is not None:
                    n_arr.append(normals[n_idx])
            vertex_arrays.append(np.array(v_arr, dtype=np.float32))
            if n_arr:
                normal_arrays.append(np.array(n_arr, dtype=np.float32))
        
        tris = []
        for i in range(0, len(vertex_arrays),3):
            tris.append(primitives.Triangle(vertex_arrays[i], vertex_arrays[i+1], vertex_arrays[i+2]))

        self.triangles = tris
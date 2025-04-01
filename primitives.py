import numpy as np
import numba as nb


class Primitive:
    def __init__(self):
        pass
    def intersect(self, ro : np.ndarray, rd : np.ndarray) -> np.ndarray:
        return np.ndarray(shape= (2,3), buffer = np.array([np.array([0,0,0]), np.array([0,1,0])])) #point, normal
    def uv(self, p : np.ndarray):
        return np.ndarray(shape=(2), buffer=np.zeros(2))


class Triangle(Primitive):
    vertices = np.array([np.array([0,0,0]), np.array([0,1,0]), np.array([1,1,0])])
    uvs = np.array([np.array([0,0]), np.array([0,1]), np.array([1,1])])

    def __init__(self, v=np.array([np.array([0,0,0]), np.array([0,1,0]), np.array([1,1,0])]), uv=np.array([np.array([0,0]), np.array([0,1]), np.array([1,1])])):
        self.vertices = v
        self.uvs = uv

    def intersect(self, ro: np.ndarray, rd: np.ndarray) -> np.ndarray:
        v0, v1, v2 = self.vertices
        edge1 = np.subtract(v1, v0)
        edge2 = np.subtract(v2, v0)
        h = np.cross(rd, edge2)
        a = np.dot(edge1, h)
        
        if np.abs(a) < 1e-8:
            return np.array([[1e10, 1e10, 1e10], [0, 0, 0]])  # No intersection case
        
        f = np.divide(1.0, a)
        s = np.subtract(ro, v0)
        u = np.multiply(f, np.dot(s, h))
        if u < 0.0 or u > 1.0:
            return np.array([[1e10, 1e10, 1e10], [0, 0, 0]])
        
        q = np.cross(s, edge1)
        v = np.multiply(f, np.dot(rd, q))
        if v < 0.0 or np.add(u, v) > 1.0:
            return np.array([[1e10, 1e10, 1e10], [0, 0, 0]])
        
        t = np.multiply(f, np.dot(edge2, q))
        if t > 1e-8:
            intersection_point = np.add(ro, np.multiply(t, rd))
            normal = np.cross(edge1, edge2)
            normal = np.divide(normal, np.linalg.norm(normal))  # Normalize the normal
            return np.array([intersection_point, normal])
        
        return np.array([[1e10, 1e10, 1e10], [0, 0, 0]])
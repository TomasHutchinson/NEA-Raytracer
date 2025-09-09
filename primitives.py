import numpy as np
import PIL
import PIL.Image
# import numba as nb

import material


class Primitive:
    albedo = [1.0,1.0,1.0]
    def __init__(self):
        pass
    def intersect(self, ro : np.ndarray, rd : np.ndarray) -> np.ndarray:
        return np.ndarray(shape= (2,3), buffer = np.array([np.array([0,0,0]), np.array([0,1,0])])) #point, normal
    def uv(self, p : np.ndarray):
        return np.ndarray(shape=(2), buffer=np.zeros(2))
    def color(self, uv):
        return np.multiply(self.albedo,[uv[0], uv[1], 1.0])[:3]


class Triangle(Primitive):
    vertices = np.array([[0, 0, 0], [0, 1, 0], [1, 1, 0]])
    uvs = np.array([
    [0, 0], [0, 1], [1, 0]])
    normals = []

    material = material.testmat

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
            return (np.array([1e10, 1e10, 1e10]), np.array([0, 0, 0]), np.array([0.0, 0.0]), np.array([0.0, 0.0, 0.0])) #`No intersection case
        
        f = np.divide(1.0, a)
        s = np.subtract(ro, v0)
        u = np.multiply(f, np.dot(s, h))
        if u < 0.0 or u > 1.0:
            return (np.array([1e10, 1e10, 1e10]), np.array([0, 0, 0]), np.array([0.0, 0.0]), np.array([0.0, 0.0, 0.0]))
        
        q = np.cross(s, edge1)
        v = np.multiply(f, np.dot(rd, q))
        if v < 0.0 or np.add(u, v) > 1.0:
            return (np.array([1e10, 1e10, 1e10]), np.array([0, 0, 0]), np.array([0.0, 0.0]), np.array([0.0, 0.0, 0.0]))
        
        t = np.multiply(f, np.dot(edge2, q))
        if t > 1e-8:
            intersection_point = np.add(ro, np.multiply(t, rd))
            normal = np.cross(edge1, edge2)
            if len(self.normals) == 3:
                u, v, w = self.barycentric_coords(intersection_point, v0, v1, v2)
                normal = self.normals[0] * u + self.normals[1] * v + self.normals[2] * w
            normal = np.divide(normal, np.linalg.norm(normal))#Normalize the normal
            uv = self.uv(intersection_point)
            color = self.color(uv)
            return ([intersection_point, normal, uv, color])
        
        return (np.array([1e10, 1e10, 1e10]), np.array([0, 0, 0]), np.array([0.0, 0.0]), np.array([0.0, 0.0, 0.0]))
    
    def uv(self, p):
        #Extract triangle vertices
        v0, v1, v2 = self.vertices[:3]
        #Compute barycentric coordinates of the position
        u, v, w = self.barycentric_coords(p, v0, v1, v2)

        #Interpolate UVs using barycentric weights
        uv0, uv1, uv2 = self.uvs[:3]
        interpolated_uv = u * uv0 + v * uv1 + w * uv2
        # interpolated_uv = interpolated_uv % 1.0
        return interpolated_uv

    def barycentric_coords(self, p, a, b, c):
        v0 = b - a
        v1 = c - a
        v2 = p - a

        d00 = np.dot(v0, v0)
        d01 = np.dot(v0, v1)
        d11 = np.dot(v1, v1)
        d20 = np.dot(v2, v0)
        d21 = np.dot(v2, v1)

        denom = d00 * d11 - d01 * d01
        v = (d11 * d20 - d01 * d21) / denom
        w = (d00 * d21 - d01 * d20) / denom
        u = 1.0 - v - w

        return u, v, w
    
    def color(self, uv):
        uv *= 3.0
        return self.material.sample_color(uv)
import numpy as np

from transform import transform


def normalize(v):
    v = np.array(v, dtype=float)
    norm = np.linalg.norm(v)
    if norm < 1e-8:
        return v
    return v / norm

class Light:
    def __init__(self, color=(1,1,1), intensity=1.0):
        self.color = np.array(color, dtype=float)
        self.intensity = float(intensity)

class DirectionalLight(Light):
    def __init__(self, direction, color=(1,1,1), intensity=1.0):
        super().__init__(color, intensity)
        self.direction = normalize(-np.array(direction, dtype=float))

    def sample(self, p, n):
        light_dir = self.direction  # from surface toward light
        dist = np.inf
        emission = np.multiply(self.color, self.intensity)
        return light_dir, dist, emission

class PointLight(Light):
    def __init__(self, position, color=(1,1,1), intensity=1.0):
        super().__init__(color, intensity)
        self.position = np.array(position, dtype=float)

    def sample(self, p, n):
        to_light = np.subtract(self.position, p)
        dist = np.linalg.norm(to_light)
        light_dir = np.divide(to_light, dist + 1e-8)
        falloff = np.divide(self.intensity, (dist*dist + 1e-8))
        emission = np.multiply(self.color, falloff)
        return light_dir, dist, emission

class AreaLight(Light):
    def __init__(self, corner1, edge1, edge2, color=(1,1,1), intensity=1.0):
        super().__init__(color, intensity)
        self.corner1 = np.array(corner1, dtype=float)
        self.edge1   = np.array(edge1, dtype=float)
        self.edge2   = np.array(edge2, dtype=float)
        self.normal  = normalize(np.cross(self.edge1, self.edge2))

    def sample(self, p, n):
        u, v = np.random.rand(2)
        pos = np.add(self.corner1, np.add(np.multiply(u, self.edge1),
                                          np.multiply(v, self.edge2)))
        to_light = np.subtract(pos, p)
        dist = np.linalg.norm(to_light)
        light_dir = np.divide(to_light, dist + 1e-8)
        emission = np.multiply(self.color, self.intensity)
        return light_dir, dist, emission
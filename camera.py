import numpy as np

import transform

class Camera:
    def __init__(self, trans, fov):
        self.transform = trans
        self.fov = fov
        self.name = "Camera"
    
    def get_ray_direction(self, uv: np.array, aspect_ratio: float) -> np.ndarray:
        fov_adjustment = np.tan(np.radians(self.fov) / 2)
        x = (2 * uv[0] - 1) * aspect_ratio * fov_adjustment
        y = (1 - 2 * uv[1]) * fov_adjustment
        direction = np.array([x, y, -1.0])


        T = self.transform.get_transformation_matrix()
        R = T[:3, :3]

        direction_world = R @ direction

        direction_world /= np.linalg.norm(direction_world)

        return direction_world
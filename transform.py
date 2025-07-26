import numpy as np

class transform:
    def __init__(self, position=None, rotation=None, scale=None):
        self.position = np.array(position if position is not None else [0.0, 0.0, 0.0], dtype=float)
        self.rotation = np.array(rotation if rotation is not None else [0.0, 0.0, 0.0], dtype=float)  # Euler radians
        self.scale = np.array(scale if scale is not None else [1.0, 1.0, 1.0], dtype=float)

    def set_rotation_degrees(self, degrees):
        self.rotation = np.radians(degrees)

    def get_rotation_degrees(self):
        return np.degrees(self.rotation)

    def get_transformation_matrix(self):
        tx, ty, tz = self.position
        rx, ry, rz = self.rotation
        sx, sy, sz = self.scale

        #Precompute sin and cos
        cx, sx_ = np.cos(rx), np.sin(rx)
        cy, sy_ = np.cos(ry), np.sin(ry)
        cz, sz_ = np.cos(rz), np.sin(rz)

        #Build the combined transformation matrix directly
        return np.array([
            [
                sx * (cz * cy),
                sx * (cz * sy_ * sx_ - sz_ * cx),
                sx * (cz * sy_ * cx + sz_ * sx_),
                tx
            ],
            [
                sy * (sz_ * cy),
                sy * (sz_ * sy_ * sx_ + cz * cx),
                sy * (sz_ * sy_ * cx - cz * sx_),
                ty
            ],
            [
                sz * (-sy_),
                sz * (cy * sx_),
                sz * (cy * cx),
                tz
            ],
            [0, 0, 0, 1]
        ])

    def transform_point(self, point):
        point_h = np.append(point, 1.0)  #Make it 4d
        transformed = self.get_transformation_matrix() @ point_h
        return transformed[:3]  #Return only 3d
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
        #scale matrix
        S = np.diag(np.append(self.scale, 1.0))

        #rotation matrices
        rx, ry, rz = self.rotation
        cos = np.cos
        sin = np.sin

        Rx = np.array([
            [1, 0,       0,      0],
            [0, cos(rx), -sin(rx), 0],
            [0, sin(rx), cos(rx),  0],
            [0, 0,       0,      1]
        ])

        Ry = np.array([
            [cos(ry),  0, sin(ry), 0],
            [0,        1, 0,       0],
            [-sin(ry), 0, cos(ry), 0],
            [0,        0, 0,       1]
        ])

        Rz = np.array([
            [cos(rz), -sin(rz), 0, 0],
            [sin(rz), cos(rz),  0, 0],
            [0,       0,        1, 0],
            [0,       0,        0, 1]
        ])

        R = Rz @ Ry @ Rx  #Rotation order: X then Y then Z
        T = np.eye(4)
        T[:3, 3] = self.position

        return T @ R @ S

    def transform_point(self, point):
        point_h = np.append(point, 1.0)  #Make it 4d
        transformed = self.get_transformation_matrix() @ point_h
        return transformed[:3]  #Return only 3d
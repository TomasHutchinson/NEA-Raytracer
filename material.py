import numpy as np
import PIL

class Material:
    albedo = (1,0,1)
    texture = []

    def __init__(self):
        self.loadtexture("textures/testimg.jpeg")

    def loadtexture(self, path : str):
        self.texture = np.divide(np.array(PIL.Image.open(path))[...,:3], 255)

    def sample(self, uv):
        uv = uv % 1.0
        uv = np.clip(uv, 0.0, 0.9999999)
        return np.multiply(self.texture[int(uv[0] * (len(self.texture)-1))][int(uv[1] * (len(self.texture[0]-1)))], self.albedo)
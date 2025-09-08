import PIL
import PIL.Image
import numpy as np
import math

class Sky():
    texture = []
    def __init__(self, texturepath):
        img = PIL.Image.open(texturepath)
        self.texture = np.divide(np.array(img)[...,:3], 255)
    
    def sample(self, p):
        radius = math.sqrt(p[0]**2 + p[2]**2)
        a = math.atan2(-p[0], p[2])
        b = math.atan2(p[1], radius)
        uv = [-(b + (math.pi/2)) / math.pi,
              (a) / (2 * math.pi)]
        return self.texture[int(uv[0] * (len(self.texture)-1))][int(uv[1] * (len(self.texture[0]-1)))]

sky = Sky("textures/nebula.jpg")
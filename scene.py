import random

import objects as obj
from transform import transform

class Scene:
    objects = [obj.mesh("meshes/cube.obj")]
    objects[0].transform = transform(rotation = [100.57,15.57,10.57], position = [0.,0.,1.])
    for i in range(0):
        m = obj.mesh("meshes/cube.obj")
        m.transform = transform(position = [random.uniform(-5, 5), random.uniform(-5, 5), random.uniform(-5, 5)], rotation = [random.randrange(-5, 5), random.randrange(-5, 5), random.randrange(-5, 5)])
        objects.append(m)

scene = Scene()
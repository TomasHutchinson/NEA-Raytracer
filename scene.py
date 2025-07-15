import objects as obj
from transform import transform

class Scene:
    objects = [obj.mesh("meshes/cube.obj")]
    objects[0].transform = transform(rotation = [100.57,15.57,10.57], position = [0.,0.,1.])

scene = Scene()
import random
import numpy as np

import objects as obj
from transform import transform
from bvh_tree import BVH

class Scene:
    objects = [obj.mesh("meshes/suzanne.obj")]
    objects[0].transform = transform(rotation = [100.57,15.57,10.57], position = [1.,1.,1.], scale = [2.,2.,2.])
    for i in range(0):
        m = obj.mesh("meshes/cube.obj")
        m.transform = transform(position = [random.uniform(-5, 5), random.uniform(-5, 5), random.uniform(-5, 5)], rotation = [random.randrange(-5, 5), random.randrange(-5, 5), random.randrange(-5, 5)])
        objects.append(m)
    
    triangles = []
    for o in objects:
        for t in o.triangles:
            verts = []
            for v in t.vertices:
                v4 = np.append(v, 1.0)
                verts.append((o.transform.get_transformation_matrix() @ v4)[:3])
            t2 = t
            t2.vertices = verts
            triangles.append(t2)
    bvh = BVH(triangles)

scene = Scene()
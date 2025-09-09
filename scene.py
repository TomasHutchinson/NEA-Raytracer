import random
import numpy as np

import objects as obj
from transform import transform
from bvh_tree import BVH
import light

class Scene:
    objects = [obj.mesh("meshes/utahteapot/teapot.obj"), obj.mesh("meshes/utahteapot/teapot.obj")]#, obj.mesh("meshes/cube.obj")]
    objects[0].transform = transform(rotation = [100.57,15.57,10.57], position = [1.,1.,-1.]) #, scale = [2.,2.,2.]
    objects[1].transform = transform(rotation = [-100.57,15.57,-10.57], position = [-3.,1.,-4.], scale = [2.,2.,2.]) 
    lights = [light.DirectionalLight((1,0.5,0.5))]

    # objects = [obj.mesh("meshes/cornellbox/cornell_box.obj")]
    # lights = [light.AreaLight((3,4,2), (3,4,3), (4,4,3),intensity=1.0/7.0, color=(14.4, 12.0, 7.2))]# light.DirectionalLight((1,0.5,0.5))
    # objects[0].transform = transform(scale = (1./100.,1./100.,1./100.), position=(2,-2,2), rotation=(0,np.pi,0))
    for i in range(0):
        m = obj.mesh("meshes/cube.obj")
        m.transform = transform(position = [random.uniform(-5, 5), random.uniform(-5, 5), random.uniform(-5, 5)], rotation = [random.randrange(-5, 5), random.randrange(-5, 5), random.randrange(-5, 5)])
        objects.append(m)
    
    triangles = []
    for o in objects:
        for t in o.triangles:
            verts = []
            normals = []
            for v in t.vertices:
                v4 = np.append(v, 1.0)
                verts.append((o.transform.get_transformation_matrix() @ v4)[:3])
            for n in t.normals:     
                M = o.transform.get_transformation_matrix()   # model -> world
                inv_transpose = np.linalg.inv(M).T     
                new_norm = (inv_transpose @ np.append(n, 0.0))[:3]
                new_norm /= np.linalg.norm(new_norm)
                normals.append(new_norm)

            t2 = t
            t2.vertices = verts
            t2.normals = normals
            triangles.append(t2)
    bvh = BVH(triangles)

scene = Scene()
import random
import numpy as np
import json

import objects as obj
from transform import transform
from bvh_tree import BVH
import light
import camera

class Scene:
    def __init__(self):
        self.objects = []
        self.lights = []
        self.triangles = []
        self.camera = camera.Camera(trans=transform(), fov=90)
        self.bvh = None

    def build_objects(self):
        teapot1 = obj.mesh("meshes/utahteapot/teapot.obj")
        teapot1.transform = transform(rotation=[100.57, 15.57, 10.57], position=[1., 1., -1.])
        teapot2 = obj.mesh("meshes/utahteapot/teapot.obj")
        teapot2.transform = transform(rotation=[-100.57, 15.57, -10.57], position=[-3., 1., -4.], scale=[2., 2., 2.])
        self.objects.extend([teapot1, teapot2])

        for i in range(0):
            m = obj.mesh("meshes/cube.obj")
            m.transform = transform(
                position=[random.uniform(-5, 5), random.uniform(-5, 5), random.uniform(-5, 5)],
                rotation=[random.randrange(-5, 5), random.randrange(-5, 5), random.randrange(-5, 5)]
            )
            self.objects.append(m)

    def build_lights(self):
        self.lights.append(light.DirectionalLight((1, 0.5, 0.5)))

    def build_triangles(self):
        """Transform object triangles into world space and collect them."""
        self.triangles = []
        for o in self.objects:
            for t in o.triangles:
                verts = []
                normals = []
                M = o.transform.get_transformation_matrix()
                inv_transpose = np.linalg.inv(M).T

                for v in t.vertices:
                    v4 = np.append(v, 1.0)
                    verts.append((M @ v4)[:3])
                for n in t.normals:
                    new_norm = (inv_transpose @ np.append(n, 0.0))[:3]
                    new_norm /= np.linalg.norm(new_norm)
                    normals.append(new_norm)

                t2 = t
                t2.vertices = verts
                t2.normals = normals
                self.triangles.append(t2)

        self.bvh = BVH(self.triangles)

    def serialize(self):
        """Convert scene to a JSON-serializable dictionary."""
        def to_list(v):
            # Convert NumPy arrays to lists
            if isinstance(v, np.ndarray):
                return v.tolist()
            return v

        def serialize_obj(o):
            return {
                "mesh_file": getattr(o, "filename", "unknown"),
                "transform": {
                    "position": to_list(o.transform.position),
                    "rotation": to_list(o.transform.rotation),
                    "scale": to_list(o.transform.scale)
                }
            }

        def serialize_light(l):
            return {
                "type": type(l).__name__,
                "color": to_list(getattr(l, "color", None)),
                "position": to_list(getattr(l, "position", None)),
                "target": to_list(getattr(l, "target", None)),
                "intensity": getattr(l, "intensity", None)
            }

        return {
            "objects": [serialize_obj(o) for o in self.objects],
            "lights": [serialize_light(l) for l in self.lights]
        }
    def save_to_file(self, filename="scene.scn"):
        with open(filename, "w") as f:
            json.dump(self.serialize(), f, indent=4)

    @classmethod
    def load_from_file(cls, filename="scene.scn"):
        with open(filename, "r") as f:
            data = json.load(f)

        scene = cls.__new__(cls)  # bypass __init__
        scene.objects = []
        scene.lights = []
        scene.triangles = []

        # Reconstruct objects
        for odata in data["objects"]:
            m = obj.mesh(odata["mesh_file"])
            tdata = odata["transform"]
            m.transform = transform(
                position=np.array(tdata["position"]),
                rotation=np.array(tdata["rotation"]),
                scale=np.array(tdata["scale"])
            )
            scene.objects.append(m)

        # Reconstruct lights
        for ldata in data["lights"]:
            ltype = ldata["type"]
            if ltype == "DirectionalLight":
                l = light.DirectionalLight(np.array(ldata["color"]))
            else:
                # Add other light types if needed
                continue
            scene.lights.append(l)

        # Rebuild triangles and BVH
        scene.build_triangles()

        return scene


# Example usage
scene = Scene()
scene.build_objects()
scene.build_triangles()
scene.save_to_file("my_scene.scn")
# Global scene instance
scene = Scene()
scene.build_lights()

def save_scene(filepath):
    scene.save_to_file(filepath)
    print(f"[scene.py] Scene saved to {filepath}")

def load_scene(filepath):
    global scene
    new_scene = Scene.load_from_file(filepath)
    scene.objects = new_scene.objects
    scene.lights = new_scene.lights
    scene.triangles = new_scene.triangles
    scene.camera = new_scene.camera
    scene.bvh = new_scene.bvh
    print(f"[scene.py] Scene loaded from {filepath}")
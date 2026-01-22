import numpy as np
import json
from primitives import Triangle

class BVH:
    root = None

    def __init__(self, scene):
        print("Building BVH")
        self.root = self.build(scene)
        print("BVH build complete")

    def trace(self, ro, rd):
        return self.root.intersect(ro,rd)
    
    def build(self, meshes, depth=0, max_leaf_size=2):
        #Compute bounding box of all meshes
        verts = []
        for m in meshes:
            for vert in m.vertices:
                verts.append(vert)
        verts = np.array(verts)

        bounds_min = np.min(verts, axis=0)
        bounds_max = np.max(verts, axis=0)
        
        node = Node(bounds=(bounds_min, bounds_max))

        #Leaf condition
        if len(meshes) <= max_leaf_size:
            node.children = meshes
            return node

        #Compute centroids
        centroids = [np.mean(m.vertices, axis=0) for m in meshes]

        #Pick longest axis
        extent = bounds_max - bounds_min
        axis = np.argmax(extent)

        #Split meshes at median centroid
        centroids_axis = [c[axis] for c in centroids]
        median = np.median(centroids_axis)

        left_meshes = [m for m, c in zip(meshes, centroids) if c[axis] <= median]
        right_meshes = [m for m, c in zip(meshes, centroids) if c[axis] > median]

        #Edge case: all go one side → force split
        if len(left_meshes) == 0 or len(right_meshes) == 0:
            left_meshes = meshes[:len(meshes)//2]
            right_meshes = meshes[len(meshes)//2:]

        #Recursive build
        node.children = [
            self.build(left_meshes, depth+1, max_leaf_size),
            self.build(right_meshes, depth+1, max_leaf_size)
        ]
        return node

    def save_to_file(self, filename):
        def serialize_node(node):
            data = {
                "bounds_min": node.bounds[0].tolist(),
                "bounds_max": node.bounds[1].tolist()
            }
            if node.children:
                data["children"] = [serialize_node(c) for c in node.children]
            else:
                # Leaf node: serialize triangles
                data["triangles"] = [
                    {
                        "vertices": [v.tolist() for v in t.vertices],
                        "normals": [n.tolist() for n in t.normals],
                        "uvs": [uv.tolist() for uv in getattr(t, "uvs", [])]
                    } for t in node.triangles
                ]
            return data

        with open(filename, "w") as f:
            json.dump(serialize_node(self.root), f, indent=4)

    @classmethod
    def load_from_file(cls, filename):
        with open(filename, "r") as f:
            data = json.load(f)

        def deserialize_node(d):
            node = Node(bounds=(np.array(d["bounds_min"]), np.array(d["bounds_max"])))
            if "children" in d:
                node.children = [deserialize_node(c) for c in d["children"]]
            else:
                node.triangles = []
                for tdata in d["triangles"]:
                    t = Triangle(
                        vertices=[np.array(v) for v in tdata["vertices"]],
                        normals=[np.array(n) for n in tdata["normals"]],
                        uvs=[np.array(uv) for uv in tdata.get("uvs", [])]
                    )
                    node.triangles.append(t)
            return node

        bvh = cls.__new__(cls)
        bvh.root = deserialize_node(data)
        return bvh


class Node:
    bounds = [(0,0,0), (1,1,1)]
    children = []

    def __init__(self, bounds):
        self.bounds = bounds

    def intersect(self, ro, rd):
        inv_dir = np.divide(1.0, rd, out=np.full_like(rd, 1e16), where=rd != 0) #in case of divide by zero
        tmin = (self.bounds[0] - ro) * inv_dir
        tmax = (self.bounds[1] - ro) * inv_dir

        t1 = np.minimum(tmin, tmax)
        t2 = np.maximum(tmin, tmax)

        t_near = np.max(t1)
        t_far = np.min(t2)

        if t_far >= t_near and t_far >= 0:
            intersections = []
            for child in self.children:
                hit = child.intersect(ro, rd)
                if hit:
                    if isinstance(child, Node):
                        intersections.extend(hit)
                    else:
                        intersections.append(hit)
            return intersections

        return [(np.array([1e10, 1e10, 1e10]), np.array([0, 0, 0]), np.array([0.0, 0.0]), np.array([0.0, 0.0, 0.0]))]
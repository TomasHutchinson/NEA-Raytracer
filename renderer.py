from PIL import Image
import time
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

#custom
import primitives
import console
import objects
import scene as scn
import sky
import light

_scene = None

def process_chunk(x_start, x_end, y_start, y_end, resolution, scene):
    chunk = np.zeros((y_end - y_start, x_end - x_start, 3), dtype=np.uint8)
    for x in range(x_start, x_end):
        for y in range(y_start, y_end):
            color = [0,0,0]
            samples = 2
            for i in range(samples):
                color = color + pixel(x / resolution[0], y / resolution[1], scene) / samples
            chunk[y - y_start, x - x_start] = (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))
    return x_start, y_start, chunk

def init_worker():
    global _scene
    print("Worker initializing scene...")
    _scene = scn.scene  # build/load it ONCE per process

def worker(i, j, x_start, x_end, y_start, y_end, resolution):
    global _scene
    x_start, y_start, chunk = process_chunk(x_start, x_end, y_start, y_end, resolution, _scene)
    return (i, j, x_start, y_start, chunk)

def render_stream(resolution: tuple, num_x_chunks=4, num_y_chunks=4):
    starttime = time.perf_counter()
    print("Start render")
    print("Loaded Scene")

    x_chunk_size = resolution[0] // num_x_chunks
    y_chunk_size = resolution[1] // num_y_chunks
    image_array = np.zeros((resolution[1], resolution[0], 3), dtype=np.uint8)

    jobs = []
    for i in range(num_x_chunks):
        x_start = i * x_chunk_size
        x_end = (i + 1) * x_chunk_size if i < num_x_chunks - 1 else resolution[0]
        for j in range(num_y_chunks):
            y_start = j * y_chunk_size
            y_end = (j + 1) * y_chunk_size if j < num_y_chunks - 1 else resolution[1]
            jobs.append((i, j, x_start, x_end, y_start, y_end, resolution))

    with ProcessPoolExecutor(
        max_workers=multiprocessing.cpu_count(),
        initializer=init_worker
    ) as executor:
        futures = [executor.submit(worker, *job) for job in jobs]
        num_completed_chunks = 0
        for future in as_completed(futures):
            i, j, x_start, y_start, chunk = future.result()
            num_completed_chunks += 1
            console.console.out(
                f"Chunk: {i}, {j} | {num_completed_chunks}/{len(jobs)} "
                f"({(num_completed_chunks/len(jobs))*100.0:.1f}%) | {time.perf_counter() - starttime:.2f}s"
            )
            # Insert the finished chunk into the array
            image_array[y_start:y_start + chunk.shape[0], x_start:x_start + chunk.shape[1]] = chunk

            # Yield a partial frame for progressive rendering
            yield Image.fromarray(image_array.copy(), mode='RGB')




def get_ray_direction(uv: np.array, fov: float, aspect_ratio: float) -> np.ndarray:
    fov_adjustment = np.tan((fov * np.pi) /180  / 2)
    x = (2 * uv[0] - 1) * aspect_ratio * fov_adjustment
    y = (1 - 2 * uv[1]) * fov_adjustment
    direction = np.array([x, y, -1])
    return np.divide(direction, np.linalg.norm(direction))

def pixel(u,v, scene):
    rd = get_ray_direction(np.array([u,v]), 90, 1.77)
    t = primitives.Triangle(np.ndarray(shape=(3,3),buffer=np.array([
    np.array([-0.5, -0.5, -1]),  # Bottom left
    np.array([0.5, -0.5, -1]),   # Bottom right
    np.array([0, 0.5, -1])       # Top
    ])))

    light = np.array([1,0.5,0.5])

    ro = np.array([0, 0, 5])

    closest_hit = np.array([[1e10, 1e10, 1e10], [0, 0, 0]])  # Default: no hit

    min_dist = np.inf

    # for obj in scene.objects:
    #     hit = obj.intersect(ro, rd)
    #     point = hit[0]
    #     if not np.allclose(point, [1e10, 1e10, 1e10]):
    #         dist = np.linalg.norm(point - ro)
    #         if dist < min_dist:
    #             min_dist = dist
    #             closest_hit = hit

    # intersection = closest_hit
    color = np.array([0.0, 0.0, 0.0])  # accumulated radiance
    throughput = np.array([1.0, 1.0, 1.0])  # energy carried by the ray
    
    max_depth = 2

    for depth in range(max_depth):
        intersections = scene.bvh.trace(ro, rd)
        if not intersections:
            # ray missed geometry
            color += throughput * sky.sky.sample(rd)
            break

        # closest hit
        intersection = min(intersections, key=lambda x: np.linalg.norm(x[0] - ro))
        if len(intersection) >= 5:
            hit_pos, normal, uv, surf_color, roughness = intersection
        else:
            hit_pos, normal, uv, surf_color = intersection
            roughness = 0.0

        normal = normalize(normal)
        surf_color = np.array(surf_color, dtype=float)
        rd = normalize(rd)

        # sanity check
        if np.linalg.norm(hit_pos) > 1e9:
            color += throughput * sky.sky.sample(rd)
            break

        # ----------------------------
        # Direct lighting with shadows
        # ----------------------------
        direct = np.zeros(3, dtype=float)
        for light in scene.lights:
            light_dir, light_dist, emission = light.sample(hit_pos, normal)

            shadow_origin = np.add(hit_pos, np.multiply(normal, 1e-4))
            shadow_hits = scene.bvh.trace(shadow_origin, light_dir)

            in_shadow = False
            if shadow_hits:
                shadow_hit = min(shadow_hits, key=lambda x: np.linalg.norm(x[0] - shadow_origin))
                hit_dist = np.linalg.norm(np.subtract(shadow_hit[0], shadow_origin))
                if light_dist == np.inf or hit_dist < light_dist:
                    in_shadow = True

            if not in_shadow:
                # ----- Diffuse (Lambertian) -----
                cos_term = max(0.0, np.dot(normal, light_dir))
                diffuse = np.multiply(surf_color, np.multiply(emission, cos_term))

                # ----- Specular (Phong-like) -----
                if roughness < 1.0:
                    view_dir = -rd
                    half_vec = normalize(np.add(light_dir, view_dir))
                    spec_angle = max(0.0, np.dot(normal, half_vec))
                    shininess = np.clip((1.0 - roughness) * 128, 1, 128)  # shinier = lower roughness
                    specular = np.multiply(emission, np.power(spec_angle, shininess))
                else:
                    specular = np.zeros(3, dtype=float)

                direct = np.add(direct, np.add(diffuse, specular))
        color = np.add(color, np.multiply(throughput, direct))

        # ----------------------------
        # Indirect bounce
        # ----------------------------
        reflect_dir = normalize(reflect(rd, normal))
        spec_prob = float(np.clip(1.0 - roughness, 0.0, 1.0))

        if np.random.rand() < spec_prob:
            # glossy/specular lobe
            new_dir = sample_phong_lobe(reflect_dir, roughness)
            throughput *= spec_prob
        else:
            # diffuse hemisphere
            new_dir = cosine_sample_hemisphere(normal)
            throughput *= surf_color * (1.0 - spec_prob)

        # offset ray origin to prevent self-intersection
        ro = hit_pos + normal * 1e-4
        rd = normalize(new_dir)

        # stop if throughput i
    
    return np.clip(color, 0.0, 1.0)

# ---- helpers ----
def normalize(v):
    n = np.linalg.norm(v)
    return v / n if n > 0 else v

def reflect(v, n):
    return v - 2.0 * np.dot(v, n) * n

def _make_basis(n):
    w = normalize(n)
    # choose a vector not parallel to w
    if abs(w[0]) > 0.999:
        a = np.array([0.0, 1.0, 0.0])
    else:
        a = np.array([1.0, 0.0, 0.0])
    v = normalize(np.cross(a, w))
    u = np.cross(w, v)
    return u, v, w

def cosine_sample_hemisphere(n):
    u1 = np.random.rand()
    u2 = np.random.rand()
    r = np.sqrt(u1)
    theta = 2.0 * np.pi * u2
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = np.sqrt(max(0.0, 1.0 - u1))   # cos(theta) for cosine-weighted
    local = np.array([x, y, z])
    u, v, w = _make_basis(n)
    world = u * local[0] + v * local[1] + w * local[2]
    return normalize(world)

def sample_phong_lobe(reflect_dir, roughness):
    # Convert roughness to Phong exponent. Tweak the multiplier if you want narrower lobes.
    expo = max(1e-4, (1.0 - roughness) * 1024.0)  # larger expo -> tighter lobe
    u1 = np.random.rand()
    u2 = np.random.rand()
    cos_theta = u1 ** (1.0 / (expo + 1.0))
    sin_theta = np.sqrt(max(0.0, 1.0 - cos_theta * cos_theta))
    phi = 2.0 * np.pi * u2
    local = np.array([sin_theta * np.cos(phi), sin_theta * np.sin(phi), cos_theta])
    u, v, w = _make_basis(reflect_dir)
    world = u * local[0] + v * local[1] + w * local[2]
    return normalize(world)
from PIL import Image
import time
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

#custom
import primitives
import console
import objects
import scene as scn
import sky


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

def render(resolution: tuple, num_x_chunks=4, num_y_chunks=4) -> Image:
    starttime = time.process_time()

    print("Start render")
    scene = scn.scene
    print("Loaded Scene")

    x_chunk_size = resolution[0] // num_x_chunks
    y_chunk_size = resolution[1] // num_y_chunks
    image_array = np.zeros((resolution[1], resolution[0], 3), dtype=np.uint8)

    tasks = []
    with ProcessPoolExecutor() as executor:
        for i in range(num_x_chunks):
            x_start = i * x_chunk_size
            x_end = (i + 1) * x_chunk_size if i < num_x_chunks - 1 else resolution[0]

            for j in range(num_y_chunks):
                y_start = j * y_chunk_size
                y_end = (j + 1) * y_chunk_size if j < num_y_chunks - 1 else resolution[1]

                # Submit each chunk as a separate process
                tasks.append(
                    executor.submit(
                        process_chunk, x_start, x_end, y_start, y_end, resolution, scene
                    )
                )

        # Collect results as they complete
        for future in as_completed(tasks):
            x_start, y_start, chunk = future.result()
            console.console.out(f"Placing chunk at ({x_start}, {y_start})")
            image_array[y_start:y_start + chunk.shape[0], x_start:x_start + chunk.shape[1]] = chunk

    print(f"Time Taken: {time.process_time() - starttime}")
    frame = Image.fromarray(image_array, mode='RGB')
    print(f"Time Taken + image: {time.process_time() - starttime}")
    return frame

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
        if not intersections or len(intersections) == 0:
            #ray missed geometry
            color += throughput * sky.sky.sample(rd)
            break

        intersection = min(intersections, key=lambda x: np.linalg.norm(x[0] - ro))
        if len(intersection) >= 5:
            hit_pos, normal, uv, surf_color, roughness = intersection
        else:
            hit_pos, normal, uv, surf_color = intersection
            roughness = 1.0

        normal = normalize(normal)
        surf_color = np.array(surf_color, dtype=float)
        rd = normalize(rd)

        if np.linalg.norm(hit_pos) > 1e9:
            color += throughput * sky.sky.sample(rd)
            break

        #lighting
        light_dir = normalize(light)
        light_intensity = max(0.0, np.dot(normal, light_dir))
        direct = surf_color * light_intensity
        color += throughput * direct

        #bounce
        reflect_dir = normalize(reflect(rd, normal))

        # Probability to sample specular = spec_prob = 1 - roughness
        spec_prob = float(np.clip(1.0 - roughness, 0.0, 1.0))
        if np.random.rand() < spec_prob:
            # Sample glossy/specular lobe around reflection
            new_dir = sample_phong_lobe(reflect_dir, roughness)
            # throughput update for specular (assume dielectric: white specular)
            # specular is not multiplied by surface albedo for dielectrics (approx).
            throughput *= spec_prob  # scale by sampling mixture weight
        else:
            # Diffuse (cosine-weighted)
            new_dir = cosine_sample_hemisphere(normal)
            # throughput update for diffuse: multiply by surface color and mixture weight
            throughput *= surf_color * (1.0 - spec_prob)

        # offset origin to avoid self-intersection
        ro = hit_pos + normal * 1e-4
        rd = normalize(new_dir)

        # tiny safety: if throughput is effectively zero, break
        if np.all(throughput < 1e-6):
            break
    
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
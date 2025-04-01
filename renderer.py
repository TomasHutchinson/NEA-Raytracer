from PIL import Image
import time
import numpy as np

#custom
import primitives

def process_chunk(x_start, x_end, y_start, y_end, resolution):
    chunk = np.zeros((y_end - y_start, x_end - x_start, 3), dtype=np.uint8)
    for x in range(x_start, x_end):
        for y in range(y_start, y_end):
            color = pixel(x / resolution[0], y / resolution[1])
            chunk[y - y_start, x - x_start] = (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))
    return x_start, y_start, chunk

def render(resolution: tuple, num_x_chunks=4, num_y_chunks=4) -> Image:
    starttime = time.process_time()
    
    x_chunk_size = resolution[0] // num_x_chunks
    y_chunk_size = resolution[1] // num_y_chunks
    image_array = np.zeros((resolution[1], resolution[0], 3), dtype=np.uint8)
    
    for i in range(num_x_chunks):
        x_start = i * x_chunk_size
        x_end = (i + 1) * x_chunk_size if i < num_x_chunks - 1 else resolution[0]
        
        for j in range(num_y_chunks):
            y_start = j * y_chunk_size
            y_end = (j + 1) * y_chunk_size if j < num_y_chunks - 1 else resolution[1]
            
            x_start, y_start, chunk = process_chunk(x_start, x_end, y_start, y_end, resolution)
            print(f"Chunk: {i}, {j}")
            image_array[y_start:y_start + chunk.shape[0], x_start:x_start + chunk.shape[1]] = chunk
    
    frame = Image.fromarray(image_array, mode='RGB')
    print(f"Time Taken: {time.process_time() - starttime}")
    return frame

def get_ray_direction(uv: np.array, fov: float, aspect_ratio: float) -> np.ndarray:
    fov_adjustment = np.tan((fov * np.pi) /180  / 2)
    x = (2 * uv[0] - 1) * aspect_ratio * fov_adjustment
    y = (1 - 2 * uv[1]) * fov_adjustment
    direction = np.array([x, y, -1])
    return np.divide(direction, np.linalg.norm(direction))

def pixel(u,v):
    rd = get_ray_direction(np.array([u,v]), 90, 1.77)
    t = primitives.Triangle(np.ndarray(shape=(3,3),buffer=np.array([
    np.array([-0.5, -0.5, -1]),  # Bottom-left
    np.array([0.5, -0.5, -1]),   # Bottom-right
    np.array([0, 0.5, -1])       # Top
    ])))

    ro = np.array([0.5, 0, 2])
    intersection = t.intersect(ro, rd)

    if np.linalg.norm(intersection[0]) < 100:
        return (1,0,0)
    return (u,v,1)
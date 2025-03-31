from PIL import Image
import time
import numpy as np

def process_chunk(x_start, x_end, resolution):
    chunk = np.zeros((resolution[1], x_end - x_start, 3), dtype=np.uint8)
    for x in range(x_start, x_end):
        for y in range(resolution[1]):
            color = pixel(x / resolution[0], y / resolution[1])
            blah = 0#sum(range(1000)) #Simulating the extra computation  PLEASE REMOVE ME
            for i in range(1000): blah += 1
            chunk[y, x - x_start] = (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))
    return x_start, chunk

def render(resolution: tuple, func, num_x_chunks=4, num_y_chunks=4) -> Image:
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
            
            x_start, y_start, chunk = process_chunk(x_start, x_end, y_start, y_end, resolution, func)
            image_array[y_start:y_start + chunk.shape[0], x_start:x_start + chunk.shape[1]] = chunk
    
    frame = Image.fromarray(image_array, mode='RGB')
    print(f"Time Taken: {time.process_time() - starttime}")
    return frame


def pixel(u,v):
    return (u,v,1)
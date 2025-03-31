from PIL import Image
import time

def render(resolution : tuple) -> Image:
    starttime = time.process_time()
    frame = Image.new(mode='RGB', size=resolution)
    print(resolution)
    for x in range(resolution[0]):
        for y in range(resolution[1]):
            color = (x/resolution[0], y/resolution[1], 255)
            frame.putpixel((x,y), (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)))
    
    print(f"Time Taken: {time.process_time() - starttime}")
    return frame
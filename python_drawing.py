import cv2
import random
import math
import os
import numpy as np
from tqdm import tqdm
import logging
import time

# Y,X
# REMEMBER!

RUNNING_ON_SERVER = int(os.environ.get("RUNNING_ON_SERVER", 1))

def main():
    if not RUNNING_ON_SERVER:
        cv2.namedWindow('image', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('image', 1000,1000)
    filename_index = 0
    amount_of_paths = 50
    save_rate = 1000

    files_produced = sorted([f for f in os.listdir("output_python/") if f.endswith('.jpg')], reverse=True)
    if files_produced:
        filename_index = int(files_produced[0].split(".")[0])
        print(f"found continue file: {filename_index}.jpg")

    eyes_x = [1649.0, 2368.0]
    eyes_y = 1997.0

    width = 4000
    height = 4000

    average_position = [0, 0] # y,x
    positions = []
    source_images = []

    display_image = 255 * np.ones(shape=[height, width, 3], dtype=np.uint8)
    white = 255 * np.ones(shape=[height, width, 3], dtype=np.uint8)

    save_image = None

    def set_pixel_bgr(y,x,bgr):
        y = int(y)
        x = int(x)
        #print(f"setting color x={x}, y={y}, color={bgr}")
        save_image[y,x, :] = bgr

    def draw_circle_on_display(y,x, radius, color):
        y = int(y)
        x = int(x)
        display_image[:,:,:] = cv2.circle(display_image, (int(x),int(y)), int(radius), color, -1)
    
    def refresh_display():
        global display_image
        display_image[:,:,:] = save_image

    def degrees_angle_between(target_y, source_y, target_x, source_x):
        return math.degrees(math.atan2(target_y - source_y, target_x - source_x))
    
    def degrees_angle_to_cos(degrees, factor):
        return math.cos(math.radians(degrees)) * factor

    def degrees_angle_to_sin(degrees, factor):
        return math.sin(math.radians(degrees)) * factor  

    class Path:
        
        def __init__(self, number):
            self.number = number
            self.is_setup = False
            self.lifespan = None

            self.source_image = None
        
        def get_source_bgr(self, y, x):
            y = int(y)
            x = int(x)
            bgr = self.source_image[y, x]
            #cv2.imshow("image", self.source_image)
            #cv2.waitKey(500)

            #print(f"getting color x={x}, y={y}, color={bgr}, image={self.source_image_index}")
            return bgr

        

        def setup(self, lifespan, source_image):
            print(f"setting up {self.number}, lifespan={lifespan}")

            self.lifespan = lifespan

            self.source_image = source_image

            eye = random.choice(eyes_x)

            y = eyes_y + random.uniform(-30,30)
            x = eye + random.uniform(-30,30)
            angle = random.randint(-360, 360) * 1.0
            self.last_point = y, x, angle
            self.is_setup = True
            if self.number == 0:
                self.behavior = 0
            else:
                self.behavior = random.choice([0,1,1,1,1,2])
            
            print(f"[{self.number}] setup: eye:{eye}, angle:{angle}, behavior:{self.behavior}")
        
        def get_next_point(self, last_point):
            y, x, angle = last_point

            #angle = (180-angle_to_center) + angle_to_first #interesting
            if self.behavior == 0:
                angle += (random.random() * 20.0) - 10.0
            if self.behavior == 1:
                pos_y, pos_x = average_position

                angle_to_center = degrees_angle_between(pos_y, y, pos_x, x)
                f_y, f_x = positions[0]
                angle_to_first = degrees_angle_between(f_y, y, f_x,x) #interesting

                angle = ((((random.randint(130,230) - angle_to_center) + angle_to_first) % 360))
            elif self.behavior == 2:
                angle += random.choice([45, -45] + [0] * 100)

            margin = random.uniform(10, 100)

            seen_green = False
            cos_x = degrees_angle_to_cos(angle, margin)
            sin_y = degrees_angle_to_sin(angle, margin)

            cand_x = x + cos_x
            cand_y = y + sin_y
            
            
            col = self.get_source_bgr(y,x)

            
            if abs(col[1] - col[-1]) > 50 or cand_x > width or cand_y > height or cand_x < 0 or cand_y < 0:
                draw_circle_on_display(cand_y, cand_x, 8, (0,0,255))
                self.lifespan = int(self.lifespan * 0.5)
                angle_to_green = degrees_angle_between(cand_y, y, cand_x, x)
                new_angle = angle + (angle_to_green * 1.0)

                print(f"[{self.number}] GREEN AVOIDANCE!!, current_angle:{angle}, angle_to_green:{angle_to_green}, new_angle: {new_angle}", flush=True)
                angle = new_angle
            
            angle = angle % 360
            speed = 1.1
            if self.number == 0:
                speed = 1.9
            cos_x = degrees_angle_to_cos(angle, speed)
            sin_y = degrees_angle_to_sin(angle, speed)

            x += cos_x
            y += sin_y
           
            return y, x, angle

        def __next__(self):
            if not self.is_setup or not self.lifespan:
                return None
            
            self.lifespan -= 1        
            self.last_point = self.get_next_point(self.last_point)
            y, x, angle = self.last_point
            bgr = self.get_source_bgr(y,x)
            set_pixel_bgr(y, x, bgr)

            if self.number == 0:
                draw_circle_on_display(y, x, 20, (0, 100, 255))
            elif self.behavior == 0:
                draw_circle_on_display(y, x, 10, (255, 0, 200))
            elif self.behavior == 1:
                draw_circle_on_display(y, x, 10, (0, 170, 250))
            elif self.behavior == 2:
                draw_circle_on_display(y, x, 10, (150, 150, 0))
            positions[self.number] = (y, x)
            #print(f"[{self.number}] x={x}, y={x}, bgr={bgr}, angle={angle}")
            return True

        def __nonzero__(self):
            return 1 if self.lifespan else 0
    
    # load images
    input_dir = 'processed/'
    for index, filename in enumerate(sorted(os.listdir(input_dir))):
        if filename.endswith('.jpg'):
            print(filename)
            source_images.append(cv2.imread(input_dir + filename))
    
    paths = [Path(i) for i in range(amount_of_paths)]
    positions.extend([[0,0] for i in range(amount_of_paths)])

    try:
        save_image = cv2.imread("output_python/{:015d}.jpg".format(filename_index))
        assert save_image is not None
    except:
        print("No file found with name: output_python/{:015d}.jpg".format(filename_index))
        save_image = 255 * np.ones(shape=[height, width, 3], dtype=np.uint8)
    
    def next_total():
        rem = (filename_index % save_rate)
        total = (save_rate - rem)
        return total
    
    pbar = tqdm(total=next_total())
    while True:
        if not RUNNING_ON_SERVER:
            key = cv2.waitKey(1)
            if key == 113:
                break

        if time.time() % 2 == 0:
            increase = 50
            save_image = np.where((255 - save_image) < increase, 255, save_image + increase)

        new_display = cv2.addWeighted(display_image, 0.95, white, 0.05, 0.0)

        new_display = cv2.addWeighted(new_display, 0.9, save_image, 0.1, 0.0)

        display_image[:,:,:] = new_display

        first = True
        for p_index, p in enumerate(paths):
            if not next(p):
                lifespan = random.randint(5, 20000)
                img = random.choice(source_images)
                p.setup(lifespan, img)
                next(p)
           
        filename_index += 1
        pbar.update(1)
        if filename_index % 50 == 0:
            resized = cv2.resize(save_image, (1600,1600), interpolation = cv2.INTER_AREA)
            cv2.imwrite("static/images/tmp.jpg".format(filename_index), resized)
            os.rename("static/images/tmp.jpg", "static/images/thumbnail.jpg")
        if filename_index % save_rate == 0:
            cv2.imwrite("output_python/{:015d}.jpg".format(filename_index), save_image)
            pbar = tqdm(total=next_total())
            if RUNNING_ON_SERVER:
                cv2.imwrite("static/images/tmp_debug.jpg".format(filename_index), display_image)
                os.rename("static/images/tmp_debug.jpg", "static/images/debug.jpg")
        average_x = int(sum([item[1] for item in positions]) / len(positions))
        average_y = int(sum([item[0] for item in positions]) / len(positions))
        average_position.clear()
        average_position.extend([average_y, average_x])
        draw_circle_on_display(average_y, average_x, 20, (0, 255, 0))
        if not RUNNING_ON_SERVER and filename_index % 5 == 0:
            cv2.imshow('image', display_image)
    
if __name__ == "__main__":
    try:
        main()
    except:
        logging.exception("error")
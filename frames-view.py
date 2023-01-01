import shutil

import sys
from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageTk
try:
    shutil.rmtree("frames-view-temp")
except:
    pass

import os

try:
    os.mkdir("frames-view-temp")
except:
    pass

fname = sys.argv[1]
# fname = "whatsapp.mp4"
import ffmpeg
(
    ffmpeg
    .input(fname)
    .output('frames-view-temp/%d.bmp', **{'vsync': 0})
    .run()
)
import numpy as np

def blur_and_subtract(im1, im2, amount):
    return ImageChops.difference(im2.filter(ImageFilter.BoxBlur(amount)), im1.filter(ImageFilter.BoxBlur(amount)))
def get_diff(im1, im2):
    diff_img = blur_and_subtract(im1, im2, 4)
    data = np.asarray(diff_img, dtype="int32")
    return data.sum()



import glob


all_images = {}

for file in glob.glob("frames-view-temp/*.bmp"):
    framenumber = int(file.split("\\")[-1].split(".")[0])
    all_images[framenumber] = Image.open(file)


print(all_images)

all_images = dict(sorted(all_images.items()))



differences_images = {}

for framenumber, image_object in all_images.items():
    for framenumber2, image_object2 in all_images.items():
        if framenumber >= framenumber2:
            continue
            # do not waste time compare 2 with 1
        dict_key = "{}-{}".format(framenumber,framenumber2)
        if dict_key in differences_images:
            continue
            # do not waste time if in diff dict
        differences_images[dict_key] = get_diff(image_object, image_object2)
        
        


differences_images = {k: v for k, v in sorted(differences_images.items(), key=lambda item: item[1])}

print(differences_images)


import ctypes
import platform
def make_dpi_aware():
    if int(platform.release()) >= 8:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)
        
make_dpi_aware()
import PySimpleGUI as sg

layout = [

        [sg.Image(key='-IMAGE-', pad=(0, 0))]
        
         ]
         
         

window = sg.Window('Loading...', layout, return_keyboard_events=True, finalize = True, element_justification='c', margins=(0,0), background_color = "#64778d")
window.Maximize()

for key in list(set("12")):
    window.bind(key, "-NUMPAD-{}-".format(key))


def loadimage(PIL_im, mode=True):
    global window
    if mode:
        ratio = min(window.size[0]//PIL_im.size[0], window.size[1]//PIL_im.size[1])
        #print(ratio)
        ratio = int(ratio)
        if ratio:
            #print(PIL_im.size[0]*ratio,PIL_im.size[1]*ratio)
            #print(window.size)
            PIL_im = PIL_im.resize((PIL_im.size[0]*ratio,PIL_im.size[1]*ratio), resample=Image.Resampling.NEAREST)
            #PIL_im = ImageOps.pad(PIL_im, window.size, color="#FF0000")
            #print(PIL_im.size)
            #print("Done")
            #image = ImageTk.PhotoImage(image=PIL_im)
            # update image in sg.Image
            #window['-IMAGE-'].update(data=image)
            #return
    else:
        PIL_im = ImageOps.contain(PIL_im, window.size)
    
    PIL_im = ImageOps.pad(PIL_im, window.size, color="#64778d")
    # Convert im to ImageTk.PhotoImage after window finalized
    image = ImageTk.PhotoImage(image=PIL_im)
    # update image in sg.Image
    window['-IMAGE-'].update(data=image)
    return
    
def get_concat_h(im1, im2):
    dst = Image.new('RGB', (im1.width + im2.width, im1.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))
    return dst

def get_concat_v(im1, im2):
    dst = Image.new('RGB', (im1.width, im1.height + im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst
    
    
grouping = {}


group_id = 0



while not len(grouping) == len(all_images):
    for key in differences_images:
        id1 = int(key.split("-")[0])
        id2 = int(key.split("-")[1])
        
        if id1 in grouping and id2 in grouping:
            # user asserted is the same. quit. 
            continue
        
        window.TKroot.title(str(grouping))
        loadimage(get_concat_v(get_concat_h(all_images[int(key.split("-")[0])], all_images[int(key.split("-")[1])]), get_concat_h(blur_and_subtract(all_images[int(key.split("-")[0])], all_images[int(key.split("-")[1])], 4),blur_and_subtract(all_images[int(key.split("-")[0])], all_images[int(key.split("-")[1])], 0))))
        while True:
            event, values = window.read(timeout=0)
            if event in (sg.WIN_CLOSED, '_EXIT_', 'Close'):
                sys.exit()
            elif event in ("-NUMPAD-{}-".format(1),):
                # they are the same
                id1 = int(key.split("-")[0])
                id2 = int(key.split("-")[1])
                
                # both in grouping. merge together
                if id1 in grouping and id2 in grouping:
                    for k,v in grouping.items():
                        if grouping[k] == grouping[id2]:
                            grouping[k] = grouping[id1]
                
                
                elif id1 in grouping and not id2 in grouping:
                    grouping[id2] = grouping[id1]
                elif id2 in grouping and not id1 in grouping:
                    grouping[id1] = grouping[id2]
                else:
                    grouping[int(key.split("-")[0])] = group_id
                    grouping[int(key.split("-")[1])] = group_id
                    group_id += 1
                break
            elif event in ("-NUMPAD-{}-".format(2),):
                # they are different
                id1 = int(key.split("-")[0])
                id2 = int(key.split("-")[1])
                
                if id1 in grouping and id2 in grouping:
                    #do not question it
                    pass
                
                
                elif id1 in grouping and not id2 in grouping:
                    grouping[id2] = group_id
                    group_id += 1
                elif id2 in grouping and not id1 in grouping:
                    grouping[id1] = group_id 
                    group_id += 1
                else:
                    grouping[id1] = group_id
                    group_id += 1
                    grouping[id2] = group_id
                    group_id += 1

                break



grouping = {k: v for k, v in sorted(grouping.items(), key=lambda item: item[1])}    
print(grouping)

for k,v in grouping.items():
    print(k, v)
    
    
    
for file in glob.glob("frames-view-temp/*.bmp"):
    framenumber = int(file.split("\\")[-1].split(".")[0])
    
    grouping_of_file = grouping[framenumber]
    
    os.rename(file, file.replace(file.split("\\")[-1], "Group{}-{}".format(str(grouping_of_file).rjust(3, "0") ,file.split("\\")[-1])))


import webbrowser
webbrowser.open("frames-view-temp")


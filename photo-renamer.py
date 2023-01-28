#!/usr/bin/env python3
# "Google photo renamer"
__author__ = "Zan Bassi"

'''
This is a script I wrote to iterate through all of my Google Photos that I downloaded to my Mac
so that I could import those photos into the Photos.app (great naming, Apple) and retain photo
information, such as the "Captured Date", and have the photos display correctly on the timeline.

At the time I downloaded my data from Google, the photos came in a "X.jpeg, X.json" file formet,
where I'd have the name of the file of a photo (or movie file), and the same filename, but a .json
file that contained more information about the photo, such as the Geo location (if available), 
Date Captured, and the device name (if available).

If you're going to use this, use it on a copy of your data first and give it a go. Please, please, PLEASE
make a backup of your precious photos before downloading some person's script from the internet and hitting "run".

Review the code. Test it on test data. If there's an issue with the code, please create an issue on
GitHub or reach out to me on Twitter @ZeroOneLabs.
'''

import os
import json
from shutil import move
from subprocess import run
from pathlib import Path
from datetime import datetime
from datetime import timedelta
from PIL import Image           # pip3 install Pillow
import piexif                   # pip3 install piexif

VERBOSE = True

ROOT_PATH = "/PATH/TO/Google_Data_Download_Folder"
GOOGLE_PHOTO_DIR = Path(f"{ROOT_PATH}/Takeout/Google Photos")
OUTPUT_DIR = Path(f"{ROOT_PATH}/Takeout/Google Photos/Modified")


dirs = [x for x in GOOGLE_PHOTO_DIR.iterdir() if x.is_dir()]

def vprint(phrase:str):
    if VERBOSE == True:
        print(phrase)


for dir in dirs:
    full_path = Path(GOOGLE_PHOTO_DIR, dir.name)

    export_dir = Path(OUTPUT_DIR, dir.name)
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # break
    files = [x for x in dir.iterdir() if x.is_file()]
    
    for file in files:
        if file.suffix == ".json" and file.name != "metadata.json":
            with open(file, "r") as f:
                jata = json.load(f)
            filename = Path(jata["title"])
            date_stamp = jata["photoTakenTime"]["formatted"]

            filepath = Path(full_path, filename)
            export_path = Path(export_dir, filename)

            # Replace "UTC" with the timecode representation, which is
            # recognized by the datetime class
            date_stamp = date_stamp.replace("UTC", "+0000")
            date_stamp_ts = datetime.strptime(date_stamp, "%b %d, %Y, %H:%M:%S %p %z")
            
            # Convert the UTC time to local CST (because I live in Chicago)
            # you can change "6" to the UTC offset for your timezone
            date_stamp_ts = date_stamp_ts - timedelta(hours=6)

            date_stamp_exif = datetime.strftime(date_stamp_ts, "%Y:%m:%d %H:%M:%S")
            
            # Exif timestamp should now look like 
            # "0000:00:00 00:00:00"
            # "YYYY:MM:DD HH:MM:SS"
            exif_dict = {'0th': {}, 'Exif': { piexif.ExifIFD.DateTimeOriginal: date_stamp_exif }, 'GPS': { }, 'Interop': {}, '1st': {}, 'thumbnail': None}
            try:
                exif_bytes = piexif.dump(exif_dict)
            except:
                print(exif_dict)
                break

            if os.path.exists(filepath):

                # Change the creation date on the file metadata
                date_creation = datetime.strftime(date_stamp_ts, "%m/%d/%Y %H:%M:%S")
                
                # run(["setfile", "-d", f"'{date_creation}'" Path(full_path, filename)], shell=True)
                if filename.suffix == ".jpg":
                    # mp4's creation and modification date was changed,
                    # so let's continue to the next loop iteration
                    # new_image = Image.open(Path(full_path, filename))
                    try:
                        piexif.insert(exif_bytes, filepath.as_posix())
                    except:
                        pass
                    # except piexif.InvalidImageDataError as e:
                    #     print(f"Error writing to file {filepath.as_posix()} with error description: {e}")
                    #     break

                # move file to export folder
                move(filepath, export_path)
                vprint(f"Setting creation date {date_creation} on file {export_path.as_posix()}.")
                run(["SetFile", "-d", f"{date_creation}", "-m", f"{date_creation}", export_path.as_posix()])


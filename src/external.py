import io
from scipy.io import loadmat,savemat
import cv2
import generic_box_pb2
import time
import os
from pathlib import Path
import numpy as np
import random


#TODO: Can change the Directories to save the data
_SUBMIT_PATH = '/dev/shm/submit/'        #.mat
_DISPLAYIMG_PATH = '/dev/shm/display/'   #.png
_DISPLAYDATA_PATH = '/tmp/display/'      #.mat


def submit():
    
    while not os.listdir(_SUBMIT_PATH):
        time.sleep(0.01)

    FileList = os.listdir(_SUBMIT_PATH)
    print(FileList)

    submitFile = _SUBMIT_PATH + random.choice(FileList)
    #Wait untill the _SUBMIT_PATH has a file to load
    while not FileIsReady(submitFile):
        time.sleep(0.01)

    with open(submitFile, 'rb') as fp:
        image_bytes = fp.read()

    return generic_box_pb2.Data(file=image_bytes),submitFile


def display(imgfile,matfile):
    #TODO:Here is where you can add your code to save the GRPC's message for Gradio to read
    dados = loadmat(io.BytesIO(imgfile)) 
    img = dados['im']
    session_hash = dados['session_hash'][0]

    UserDisplayImgPath = _DISPLAYIMG_PATH + session_hash + ".png"
    UserDisplayDataPath = _DISPLAYDATA_PATH + session_hash + ".mat"

    mat_path = Path(UserDisplayDataPath)
    MatDict = loadmat(io.BytesIO(matfile))

    img_path = Path(UserDisplayImgPath)
    while img_path.is_file():
        time.sleep(0.01)

    if ('frame_00000' in MatDict) or (not mat_path.is_file()):
        savemat(UserDisplayDataPath, MatDict)
    else:
        while not FileIsReady(UserDisplayDataPath):
            time.sleep(0.01)

        oldMatDict = loadmat(UserDisplayDataPath)
        MatAppend(oldMatDict,MatDict,UserDisplayDataPath)

    cv2.imwrite(UserDisplayImgPath, img) 

    return


'''------------------------------------------Auxiliary Functions--------------------------------------------------------'''

#Function to Clean up files
def cleanup(dir,wait):
    
    # Delay the cleanup to ensure the files have been sent
    time.sleep(wait)

    my_file = Path(dir)
    #Make sure the file is in directory
    if my_file.is_file():
        # Delete the temporary directory
        os.remove(dir)


'''Helper function to make sure a file is ready to read
        Due to the asyncronous behaviour between the gradio and GRPC servers,
        It's useful to have a function that makes sure a file is fully written.
'''
def FileIsReady(path):
    my_file = Path(path)

    #Make sure the file is in directory
    if not my_file.is_file():
        return False

    #Check if the file size changes
    #if it does we assume its still being written
    file_size = my_file.stat().st_size
    time.sleep(0.1)
    new_size = my_file.stat().st_size

    #if file size hasn't changed we return True
    if new_size == file_size:
        return True
    
    return False


def MatAppend(existing_data, new_data, output_path):

    existing_data.pop('__header__', None)
    existing_data.pop('__version__', None)
    existing_data.pop('__globals__', None)
    new_data.pop('__header__', None)
    new_data.pop('__version__', None)
    new_data.pop('__globals__', None)
    
    # Merge the data
    for key, value in new_data.items():
        existing_data[key] = value
    
    # Save the merged data into a new .mat file
    savemat(output_path, existing_data)
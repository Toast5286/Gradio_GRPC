import gradio as gr
from scipy.io import savemat,loadmat
import time
import io
import cv2

from external import cleanup,FileIsReady,_DISPLAY_PATH,_SUBMIT_PATH

#Define the Gradio Interface
def gradio_function():

    #TODO: Here is where you can add your code to change the Gradio Interface
    demo = gr.Interface(
    fn=gradio_GRPC_display,
    inputs=gr.Image(),
    outputs=gr.Image(),
    )

    demo.launch()

#Function used to process the users data and outputs the desired data for the user
def gradio_GRPC_display(inputImg):
    #TODO: Here is where you can add your code to change how you process Gradios inputs and how to read GRPC's saved data
    if (inputImg is None):
        return
    #Make sure the Display directory is cleared
    cleanup("Disp",0)
    
    #Save file in memory so GRPC can access it
    data_dict = {'im': inputImg}
    savemat(_SUBMIT_PATH, data_dict)

    #Wait untill the display images is saved
    while not FileIsReady(_DISPLAY_PATH):
        time.sleep(0.1)

    return _DISPLAY_PATH

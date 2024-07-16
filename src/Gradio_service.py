import gradio as gr
from scipy.io import savemat,loadmat
import time

from external import cleanup,FileIsReady,_DISPLAYIMG_PATH,_DISPLAYDATA_PATH,_SUBMIT_PATH

#Define the Gradio Interface
def gradio_function():

    #TODO: Here is where you can add your code to change the Gradio Interface
    with gr.Blocks() as demo:
        img = gr.Image(sources="webcam",streaming=True)
        yoloImg = gr.Image()

        img.stream(gradio_GRPC_display,inputs=img,outputs=[yoloImg])

    demo.launch()

#Function used to process the users data and outputs the desired data for the user
def gradio_GRPC_display(inputImg):
    #TODO: Here is where you can add your code to change how you process Gradios inputs and how to read GRPC's saved data
    if (inputImg is None):
        return
    #Make sure the Display directory is cleared
    cleanup("DispImg",0)
    cleanup("DispMat",0)
    
    #Save file in memory so GRPC can access it
    data_dict = {'im': inputImg}
    savemat(_SUBMIT_PATH, data_dict)

    #Wait untill the display images is saved
    while not FileIsReady(_DISPLAYIMG_PATH):
        time.sleep(0.01)

    return _DISPLAYIMG_PATH

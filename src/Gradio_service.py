import gradio as gr
from scipy.io import savemat,loadmat
import time
import cv2
from pathlib import Path

from external import cleanup,FileIsReady,_DISPLAYIMG_PATH,_DISPLAYDATA_PATH,_SUBMIT_PATH

#Define the Gradio Interface
def gradio_function():

    #TODO: Here is where you can add your code to change the Gradio Interface
    with gr.Blocks() as demo:

        streamFrame = gr.Number(value=0,visible=False,interactive=False)

        with gr.Row():
            with gr.Column():
                input_type = gr.Dropdown(choices=["Image", "Stream", "Video"], label="Select Input Type")

                with gr.Column(visible=False) as Image_input:
                    img = gr.Image(sources="upload")
                with gr.Column(visible=False) as Stream_input:
                    stream = gr.Image(sources="webcam",streaming=True)
                    resetFrameCount = gr.Button(value='Reset frame Count')
                with gr.Column(visible=False) as Video_input:
                    vid = gr.Video()

            
            with gr.Column():
                display = gr.Image(label="YoloV8n Output")
                fileOutput = gr.File(label='Output .mat file')

        input_type.change(update_visibility,inputs=input_type,outputs=[Image_input,Stream_input,Video_input])
        
        img.change(gradio_GRPC_submit,inputs=[img,input_type],outputs=[display,fileOutput])     
        stream.stream(gradio_GRPC_Streamsubmit,inputs=[stream,input_type,streamFrame],outputs=[streamFrame,display,fileOutput])
        vid.change(gradio_GRPC_Vidsubmit,inputs=[vid,input_type],outputs=[display,fileOutput])

        resetFrameCount.click(ResetStreamFrameCount,inputs=[],outputs=[streamFrame])
        
    demo.launch()


def update_visibility(input_type):
    return gr.update(visible=input_type == "Image"), gr.update(visible=input_type == "Stream"), gr.update(visible=input_type == "Video")

#-----Image---------------------------------

#Function used to process the users data and outputs the desired data for the user
def gradio_GRPC_submit(inputImg,input_type,req:gr.Request):
    UserSubPath = _SUBMIT_PATH + req.session_hash + ".mat"
    UserDisplayImgPath = _DISPLAYIMG_PATH + req.session_hash + ".png"
    UserDisplayDataPath = _DISPLAYDATA_PATH + req.session_hash + ".mat"

    #Make sure the Display directory is cleared
    cleanup(UserDisplayImgPath,0)
    

    if input_type == "Image" and not (inputImg is None):

        sub_file = Path(UserSubPath)
        while sub_file.is_file():
                time.sleep(0.01)

        #Save file in memory so GRPC can access it
        data_dict = {'im': inputImg,'frame': 0,'session_hash':req.session_hash}
        savemat(UserSubPath, data_dict)

    return gradio_GRPC_display(UserDisplayImgPath,UserDisplayDataPath)

#-----Stream---------------------------------

#Function used to process the users data and outputs the desired data for the user
def gradio_GRPC_Streamsubmit(inputImg,input_type,frame,req:gr.Request):
    UserSubPath = _SUBMIT_PATH + req.session_hash + ".mat"
    UserDisplayImgPath = _DISPLAYIMG_PATH + req.session_hash + ".png"
    UserDisplayDataPath = _DISPLAYDATA_PATH + req.session_hash + ".mat"

    #Make sure the Display directory is cleared
    cleanup(UserDisplayImgPath,0)
    
    if input_type == "Stream" and not (inputImg is None):
        sub_file = Path(UserSubPath)
        while sub_file.is_file():
                time.sleep(0.01)

        #Save file in memory so GRPC can access it
        data_dict = {'im': inputImg,'frame': frame,'session_hash':req.session_hash}
        savemat(UserSubPath, data_dict)

        imagePath,filePath = gradio_GRPC_display(UserDisplayImgPath,UserDisplayDataPath)
        
        return frame + 1,imagePath,filePath

def ResetStreamFrameCount():
    return 0

#-----Video---------------------------------

#Function used to process the users data and outputs the desired data for the user
def gradio_GRPC_Vidsubmit(inputVid,input_type,req:gr.Request):  
    if (inputVid is None) or (input_type != "Video"):
        return
    
    UserSubPath = _SUBMIT_PATH + req.session_hash + ".mat"
    UserDisplayImgPath = _DISPLAYIMG_PATH + req.session_hash + ".png"
    UserDisplayDataPath = _DISPLAYDATA_PATH + req.session_hash + ".mat"
    
    sub_file = Path(UserSubPath)
    cap = cv2.VideoCapture(inputVid)
    amount_of_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    for i in range(amount_of_frames):

        #Make sure the Display directory is cleared
        cleanup(UserDisplayImgPath,0)
    

        #Make sure last frame has been sent to yolo
        while sub_file.is_file():
            time.sleep(0.01)
        
        #read frame
        _, frame = cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        #Save file in memory so GRPC can access it
        data_dict = {'im': frame,'frame': i,'session_hash':req.session_hash}
        savemat(UserSubPath, data_dict)

        yield gradio_GRPC_display(UserDisplayImgPath,UserDisplayDataPath)

#-----Display---------------------------------


#Function used to process the users data and outputs the desired data for the user
def gradio_GRPC_display(UserDisplayImgPath,UserDisplayDataPath):

    timeOut = 0
    #Wait untill the display images is saved
    while not FileIsReady(UserDisplayImgPath):
        time.sleep(0.01)
        timeOut = timeOut+1
        if  timeOut == 100:
            return None, None

    return UserDisplayImgPath, UserDisplayDataPath


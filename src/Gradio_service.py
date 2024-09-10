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
        demo.unload(delete_directory)
        
    demo.launch()


def update_visibility(input_type):
    return gr.update(visible=input_type == "Image"), gr.update(visible=input_type == "Stream"), gr.update(visible=input_type == "Video")

#-----Image---------------------------------

#Function used to process the users data and outputs the desired data for the user
def gradio_GRPC_submit(inputImg,input_type,req:gr.Request):
    #Make sure it's the right input
    if (input_type != "Image") or (inputImg is None):
        return None, None
    
    #Get necessary paths
    UserSubPath,UserDisplayImgPath,UserDisplayDataPath = get_Paths(req.session_hash)

    #Make sure the Display directory is cleared before sending the next image
    cleanup(UserDisplayImgPath,0)

    #Save the images for grpc's submit function
    Wait_And_Save(UserSubPath,inputImg,0,req.session_hash)

    #Wait to get the images and .mat file to display
    return Wait_And_Display(UserDisplayImgPath,UserDisplayDataPath,3000)

#-----Stream---------------------------------

#Function used to process the users data and outputs the desired data for the user
def gradio_GRPC_Streamsubmit(inputImg,input_type,frame,req:gr.Request):
    #Make sure it's the right input
    if (input_type != "Stream") or (inputImg is None):
        return frame,None, None
    
    #Get necessary paths
    UserSubPath,UserDisplayImgPath,UserDisplayDataPath = get_Paths(req.session_hash)

    #Make sure the Display directory is cleared before sending the next image
    cleanup(UserDisplayImgPath,0)

    #Save the images for grpc's submit function
    Wait_And_Save(UserSubPath,inputImg,frame,req.session_hash)

    #Wait to get the images and .mat file to display
    imagePath,filePath = Wait_And_Display(UserDisplayImgPath,UserDisplayDataPath,3000)
        
    return frame + 1,imagePath,filePath

def ResetStreamFrameCount(req:gr.Request):
    delete_directory(req)
    return 0

#-----Video---------------------------------

#Function used to process the users data and outputs the desired data for the user
def gradio_GRPC_Vidsubmit(inputVid,input_type,req:gr.Request):  
    if (input_type != "Video") or (inputVid is None):
        return None, None
    
    #Get necessary paths
    UserSubPath,UserDisplayImgPath,UserDisplayDataPath = get_Paths(req.session_hash)
    
    #Get vid object and respective frame count
    cap = cv2.VideoCapture(inputVid)
    amount_of_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    for i in range(amount_of_frames):

        #Make sure the Display directory is cleared
        cleanup(UserDisplayImgPath,0)

        #read frame
        _, frame = cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        #Save the images for grpc's submit function
        Wait_And_Save(UserSubPath,frame,i,req.session_hash)

        yield Wait_And_Display(UserDisplayImgPath,UserDisplayDataPath,3000)

#-----delete_directory-------------------------------

def delete_directory(req:gr.Request):
     #Get necessary paths
    _,UserDisplayImgPath,UserDisplayDataPath = get_Paths(req.session_hash)
    cleanup(UserDisplayImgPath,0)
    cleanup(UserDisplayDataPath,0)

'''------------------------------------------Auxiliary Functions--------------------------------------------------------'''
        
def get_Paths(session_hash):
    UserSubPath = _SUBMIT_PATH + session_hash + ".mat"
    UserDisplayImgPath = _DISPLAYIMG_PATH + session_hash + ".png"
    UserDisplayDataPath = _DISPLAYDATA_PATH + session_hash + ".mat"

    return UserSubPath,UserDisplayImgPath,UserDisplayDataPath
        
def Wait_And_Save(SavePath,image,frame,session_hash):
    sub_file = Path(SavePath)
    while sub_file.is_file():
            time.sleep(0.01)

    #Save file in memory so GRPC can access it
    data_dict = {'im': image,'frame': frame,'session_hash':session_hash}
    savemat(SavePath, data_dict)


#Function used to process the users data and outputs the desired data for the user
def Wait_And_Display(UserDisplayImgPath,UserDisplayDataPath,timeOutLimit):

    timeOut = 0
    #Wait untill the display images is saved
    while not FileIsReady(UserDisplayImgPath):
        time.sleep(0.01)
        timeOut = timeOut+1
        if  timeOut >= timeOutLimit:
            return None, None

    return UserDisplayImgPath, UserDisplayDataPath
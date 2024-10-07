import gradio as gr
from PIL import Image
from scipy.io import savemat,loadmat
import time
import cv2
import numpy as np
import io
from pathlib import Path

from external import cleanup,FileIsReady,_DISPLAYIMG_PATH,_DISPLAYDATA_PATH,_SUBMIT_PATH

#Define the Gradio Interface
def gradio_function():
    '''
    * Function:     gradio_function
    * Arguments:    
    *
    * Returns:
    *
    * Description:  Function to run the gradio user interface
    '''

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
    '''
    * Function:     gradio_GRPC_submit
    * Arguments:    inputImg (Gradio Image)                 -The input image that the user submited
    *               input_type (Gradio Dropdown)            -The input type (image, Stream or Video) that the user selected
    *               req (Gradio Request)                    -The Users information (like the session hash)
    *               
    * Returns:       UserDisplayImgPath                     -The Path to the Ploted image
    *                UserDisplayDataPath                    -The Path to the file to display
    *
    * Description:  Funtion that is called when a user submits a image to be processed. It saves the image in to a .mat file and saves it to the submit file. Afterwards, it waits untill the pipeline returns a new .mat file in the display directories and displays them.
    '''
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
    '''
    * Function:     gradio_GRPC_Streamsubmit
    * Arguments:    inputImg (Gradio Image with source as webcam)   -The input image that the user submited
    *               input_type (Gradio Dropdown)                    -The input type (image, Stream or Video) that the user selected
    *               frame (Gradio Number)                           -The number of frames already streamed
    *               req (Gradio Request)                            -The Users information (like the session hash)
    *               
    * Returns:       frame+1                                        -The new number of frames
    *                imagePath                                      -The Path to the Ploted image
    *                filePath                                       -The Path to the file to display
    *
    * Description:  Funtion that is called when a user submits the webcam image to be processed. It saves the image in to a .mat file and saves it to the submit file. Afterwards, it waits untill the pipeline returns a new .mat file in the display directories and displays them.
    '''
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
    '''
    * Function:     ResetStreamFrameCount
    * Arguments:    req (Gradio Request)                            -The Users information (like the session hash)
    *               
    * Returns:       0                                              -The new frame count. It was reset, therefore it is now 0
    *
    * Description:  Clears the frame count and, therefore also deletes all the .mat files related to this user.
    '''
    delete_directory(req)
    return 0

#-----Video---------------------------------

#Function used to process the users data and outputs the desired data for the user
def gradio_GRPC_Vidsubmit(inputVid,input_type,req:gr.Request):  
    '''
    * Function:     gradio_GRPC_Vidsubmit
    * Arguments:    inputVid (Gradio Video)                         -The input video that the user submited
    *               input_type (Gradio Dropdown)                    -The input type (image, Stream or Video) that the user selected
    *               req (Gradio Request)                            -The Users information (like the session hash)
    *               
    * Returns:       imagePath                                      -The Path to the Ploted image
    *                filePath                                       -The Path to the file to display
    *
    * Description:  Funtion that is called when a user submits a video to be processed. It saves each frame in to a .mat file and saves it to the submit file. Afterwards, it waits untill the pipeline returns a new .mat file in the display directories and displays them.
    *               This process can "Freeze" the rest of the useres untill the video is completly prosessed.
    '''
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
    '''
    * Function:     delete_directory
    * Arguments:    req (Gradio Request)                            -The Users information (like the session hash)
    *               
    * Returns:
    *
    * Description:  Clears the user's directory.
    '''
     #Get necessary paths
    _,UserDisplayImgPath,UserDisplayDataPath = get_Paths(req.session_hash)
    cleanup(UserDisplayImgPath,0)
    cleanup(UserDisplayDataPath,0)

'''------------------------------------------Auxiliary Functions--------------------------------------------------------'''
        
def get_Paths(session_hash):
    '''
    * Function:     get_Paths
    * Arguments:    session_hash                            -The User's session hash
    *               
    * Returns:      UserSubPath                             -User's .mat file path to submit image
    *               UserDisplayImgPath                      -User's .mat file path to receive and display ploted image
    *               UserDisplayDataPath                     -User's .mat file path to receive and display data
    *
    * Description:  Gets the user's usefull paths
    '''
    UserSubPath = _SUBMIT_PATH + session_hash + ".mat"
    UserDisplayImgPath = _DISPLAYIMG_PATH + session_hash + ".png"
    UserDisplayDataPath = _DISPLAYDATA_PATH + session_hash + ".mat"

    return UserSubPath,UserDisplayImgPath,UserDisplayDataPath
        
def Wait_And_Save(SavePath,image,frame,session_hash):
    '''
    * Function:     Wait_And_Save
    * Arguments:    SavePath                                -The path to the .mat file to save the image and useful information
    *               image                                   -The image to save in to the .mat file
    *               frame                                   -The number of the frame that is going to be saved in to the .mat file
    *               session_hash                            -The User's session hash
    *               
    * Returns:
    *
    * Description:  Waits for the SavePath to be clear (in case the grpc is delayed), creates a dictionary with the image, frame number and session hash and save it to the SavePath.
    '''
    sub_file = Path(SavePath)
    while sub_file.is_file():
            time.sleep(0.01)

    #Save file in memory so GRPC can access it
    JPEGImage =  SaveJPEGImage(image)
    data_dict = {'im': JPEGImage,'frame': frame,'session_hash':session_hash}
    savemat(SavePath, data_dict)


#Function used to process the users data and outputs the desired data for the user
def Wait_And_Display(UserDisplayImgPath,UserDisplayDataPath,timeOutLimit):
    '''
    * Function:     Wait_And_Display
    * Arguments:    UserDisplayImgPath                      -The path where grpc saved the .mat file that has the ploted image to display
    *               UserDisplayDataPath                     -The path where grpc saved the .mat file that has the data to display
    *               timeOutLimit                            -number of attempts that the function can try before getting a time out (to avoid infinite loops)
    *               
    * Returns:      UserDisplayImgPath                      -The path where grpc saved the .mat file that has the ploted image to display
    *               UserDisplayDataPath                     -The path where grpc saved the .mat file that has the data to display
    *
    * Description: Waits untill there's a file written in UserDisplayImgPath. Afterwards it returns them as they are ready to be displayed
    '''

    timeOut = 0
    #Wait untill the display images is saved
    while not FileIsReady(UserDisplayImgPath):
        time.sleep(0.01)
        timeOut = timeOut+1
        if  timeOut >= timeOutLimit:
            return None, None
        
    mat_file = Path(UserDisplayDataPath)
    if mat_file.is_file():
        return UserDisplayImgPath, UserDisplayDataPath
    else:
        return UserDisplayImgPath, None

def SaveJPEGImage(input_image):
    '''
    * Function:     SaveJPEGImage
    * Arguments:    input_image                             -The image to save in JPEG format

    *               
    * Returns:      jpeg_image_array                        -The image in JPEG format
    *
    * Description: Saves numpy array in to a JPEG format
    '''
    #Save image in JPEG format in memory buffer
    jpeg_image_io = io.BytesIO()  # In-memory buffer
    image = Image.fromarray(input_image)
    image.save(jpeg_image_io, format='JPEG')
    
    #Get the JPEG encoded bytes
    jpeg_image_bytes = jpeg_image_io.getvalue()

    #Convert the bytes to a numpy array for saving into .mat
    jpeg_image_array = np.frombuffer(jpeg_image_bytes, dtype=np.uint8)

    return jpeg_image_array
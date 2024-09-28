
# Gradio_GRPC

A simple and flexible Gradio Interface for GRPC pipelines. This interface runs a GRPC server asynchronously with a Gradio server.

## Gradio functions

All Gradio functions are stored in the "Gradio_service.py" file. It contains the main gradio function, 3 input functions (for each type of input) and 5 auxiliary functions.

**gradio_function**:
Used to define the aesthetic of the interface and launch the Gradio server.

**gradio_GRPC_submit, gradio_GRPC_Streamsubmit and gradio_GRPC_Vidsubmit**
Used to save Gradio's inputs (images/frames) in to a .mat file (for the GRPC's submit functions to read) and waits for the Display files (sent by the GRPC's display function) to show to the user.
The .mat file submitted has the following structure:

```bash
[session_hash].mat (dictionary)
  ├── ”im” - numpy array containing the saved image/frame;
  ├── ”frame” – number of the frame of uploaded image image (0 in case of a single image). This information is used for appending the the receiving .mat files in GRPC display;
  └── ”session_hash” – unique identifier for the user’s web page.

```

There 2 received .mat files. The image.mat file (used to send the plotted image to display) and the data.mat file (used to share a .mat file with the user).
The .mat files received has the following structure:

```bash
image.mat (dictionary)
   ├── ”im” - numpy array containing the image to be shown to the user;
   └── ”session_hash” – the user’s unique identifier that indicates to whom should the image be displayed to.
```
```bash
data.mat (dictionary)
   ├── ”data_00000” – Dictionary containing the information for frame 0; (This is optional, but must exist if appending is needed for future files);
   └── …
```

**Auxiliary Functions**
Other functions are used for cleanup, getting paths to directories (get_Paths), saving files (Wait_And_Save) and receiving them (Wait_And_Display). More description on the code’s comments.

## GRPC functions

All GRPC functions are stored in the "external.py" file. It contains 5 difrente functions. 

**submit**:
Used to create a GRPC message (of type Data) with the inputs from Gradio's interface. The .mat file that is sent in Data message is the same as saved in the submit directory. If using one of the gradio_GRPC_submit functions, then it’ll have the same structure as [session_hash].mat :

```bash
[session_hash].mat (dictionary)
  ├── ”im” - numpy array containing the saved image/frame;
  ├── ”frame” – number of the frame of uploaded image image (0 in case of a single image). This information is used for appending the the receiving .mat files in GRPC display;
  └── ”session_hash” – unique identifier for the user’s web page.

```


**display**:
Used to save the data from a GRPC's message to a file for Gradio to display on its output. The files must follow the structure of the 2 received .mat files defined in the gradio_GRPC_submit functions:

```bash
image.mat (dictionary)
   ├── ”im” - numpy array containing the image to be shown to the user;
   └── ”session_hash” – the user’s unique identifier that indicates to whom should the image be displayed to.
```
```bash
data.mat (dictionary)
   ├── ”data_00000” – Dictionary containing the information for frame 0; (This is optional, but must exist if appending is needed for future files);
   └── …
```

**cleanup**:
Used to remove direcories used to share data between the Gradio server and the GRPC server. 
This function is used at the start of the gradio_GRPC_display function to clear the the "Display" directory and after sending the GRPC message from the submit function. Also used to clean up after the user closed the web UI.

**FileIsReady**:
Used as a auxiliary function to make sure the files sent between the Gradio and GRPC's functions are fully written. This function is essential due to the asyncronous nature between the Gradio server and the GRPC server.

**MatAppend**
Used as auxiliary function to append the newly received data.mat file to the previous data.mat file from older GRPC messages. Saves this new .mat file to the desired output path.


## Deploy

To deploy this program it needes to compile the GRPC with the folowing command:

```bash
  python -m grpc_tools.protoc --proto_path=./protos --python_out=. --grpc_python_out=. generic_box.proto
```
To create the Docker image with the program use:

```bash
    docker build -t gradio_grpc  --build-arg SERVICE_NAME=generic_box -f docker/Dockerfile .
```

To run the container run the command:

```bash
    docker run -p 8061:8061 -p 7860:7860 -it --rm gradio_grpc
```

Where it maps the port 8061 to the GRPC and port 7860 to the Gradio server. In the command line will be a link to the Gradio WebUI. With the default settings it runs as localhost:7860.



## Testing

The file "test__generic_box.ipynb" is a jupyterNotebook with the test code.

1. Open your browser and go to "localhost:7860". This should open Gradio's WebUI. 

2. Afterwards open the "test__generic_box.ipynb" file in your computer and run all.

3. If correctly set up, the jupyterNotebook will wait untill a image is submited in Gradio's WebUI and display it. 

4. After this, the jupyterNotebook will send a image and Gradio's WebUI should show it.


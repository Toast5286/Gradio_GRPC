
# Gradio_GRPC

A simple and flexible Gradio Interface for GRPC. This interface runs a GRPC server asynchronously with a Gradio server.

## Gradio functions

All Gradio functions are stored in the "Gradio_service.py" file. It contains 2 difrente functions. 

**gradio_function**:
Used to define the astetic of the interface and launch the Gradio server.

**gradio_GRPC_display**:
Used to save Gradio's inputs in to a .mat file (for the GRPC's submit functions to read) and waits for the Display files (sent by the GRPC's display function) to show to the user.

## GRPC functions

All GRPC functions are stored in the "external.py" file. It contains 4 difrente functions. 

**submit**:
Used to create a GRPC message (of type Data) with the inputs from Gradio's interface.   

**display**:
Used to save the data from a GRPC's message to a file for Gradio to display on its output.

**cleanup**:
Used to remove direcories used to share data between the Gradio server and the GRPC server. 
This function is used at the start of the gradio_GRPC_display function to clear the the "Display" directory and after sending the GRPC message from the submit function.

**FileIsReady**:
Used as a auxiliary function to make sure the files sent between the Gradio and GRPC's functions are fully written. This function is essential due to the asyncronous nature between the Gradio server and the GRPC server.


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


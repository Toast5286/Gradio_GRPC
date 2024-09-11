import concurrent.futures as futures
import grpc
import grpc_reflection.v1alpha.reflection as grpc_reflection
import logging
import generic_box_pb2
import generic_box_pb2_grpc
import utils
import os

import threading
import asyncio
from Gradio_service import gradio_function


class ServiceImpl(generic_box_pb2_grpc.GenericBoxServiceServicer):

    def __init__(self,display_function,submit_function,cleanup_function):
        """
        Args:
            calling_function: the function that should be called
                              when a new request is received

                              the signature of the function should be:

                              (image: bytes) -> bytes

                              as described in the process method

        """
        self.__display_fn = display_function
        self.__submit_fn = submit_function
        self.__cleanup_fn = cleanup_function

    def display(self, request: generic_box_pb2.PlotInfo, context):
        """Processes a given ImageWithPoses request

        It expects that a process function was already registered
        with the following signature

        (image: bytes) -> bytes

        Image is the bytes of the image to process.

        Args:
            request: The ImageWithPoses request to process
            context: Context of the gRPC call

        Returns:
            The Image with the applied function

        """
        image = request.img.file
        matFile = request.file.file
        try:
            self.__display_fn(image,matFile)
        except:
            logging.exception(f'''[ERRO NO DISPLAY]''')

        return generic_box_pb2.Empty()
    
    def submit(self, request: generic_box_pb2.Empty, context):
        """Processes a given ImageWithPoses request

        It expects that a process function was already registered
        with the following signature

        (image: bytes) -> bytes

        Image is the bytes of the image to process.

        Args:
            request: The ImageWithPoses request to process
            context: Context of the gRPC call

        Returns:
            The Image with the applied function

        """
        result,submitFile = self.__submit_fn()
        #Clear submit direcory
        self.__cleanup_fn(submitFile,0)
        return result

def grpc_server():
    logging.basicConfig(
        format='[ %(levelname)s ] %(asctime)s (%(module)s) %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO)

    display_function = utils.get_calling_function('display')
    submit_function = utils.get_calling_function('submit')
    cleanup_function = utils.get_calling_function('cleanup')
    if not display_function or not submit_function or not cleanup_function:
        exit(1)

    server = grpc.server(futures.ThreadPoolExecutor())
    generic_box_pb2_grpc.add_GenericBoxServiceServicer_to_server(
        ServiceImpl(display_function,submit_function,cleanup_function),
        server)

    # Add reflection
    service_names = (
        generic_box_pb2.DESCRIPTOR.services_by_name['GenericBoxService'].full_name,
        grpc_reflection.SERVICE_NAME
    )
    grpc_reflection.enable_server_reflection(service_names, server)

    utils.run_server(server)

async def main():
    grpc_thread = threading.Thread(target=grpc_server)
    grpc_thread.start()

    # Launch Gradio in the main thread as it's non-blocking
    await gradio_function()

        

if __name__ == '__main__':
    if not os.path.exists('/dev/shm/submit/'):
        os.makedirs('/dev/shm/submit/')
    if not os.path.exists('/dev/shm/display/'):
        os.makedirs('/dev/shm/display/')
    if not os.path.exists('/tmp/display/'):
        os.makedirs('/tmp/display/')

    asyncio.run(main())

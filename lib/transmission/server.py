import os
import logging
import socket
import threading
import subprocess
from typing import Any
from lib.utils.timestamp import get_time



class Server:

    def __init__(self, params: Any, port: int = 7024):
        self.HEADER = 100
        self.PORT = port
        # self.SERVER = socket.gethostbyname('david.fritz.box')
        self.SERVER = '192.168.31.236'
        self.ADDR = (self.SERVER, self.PORT)
        self.FORMAT = 'utf-8'
        self.DISCONNECT_MESSAGE = '!DISCONNECT'
        self.DATA_DIR = '/home/alfred/Projects/Security_Cameras/Data/Test_Connection/images'


    def get_the_video(self, connection, address):

        connected = True
        while connected:
            msg_length = connection.recv(self.HEADER).decode(self.FORMAT)
            if msg_length:
                try:
                    print(f'Msg Length {msg_length} {int(msg_length)}')
                    logging.debug(f'[{get_time()}] [{address}] Msg Length {msg_length}.')

                    msg_length = int(msg_length)
                    msg = connection.recv(msg_length).decode(self.FORMAT)

                    logging.debug(f'[{get_time()}] [{address}] {msg}')

                    if msg == self.DISCONNECT_MESSAGE:
                        connected = False
                        continue

                    file_name = msg.rsplit('/', 1)[1]

                    if file_name not in os.listdir(self.DATA_DIR):
                        logging.debug(f'[{get_time()}] [{address}] Starting the copy command {msg}:{file_name}.')
                        status = subprocess.run(
                            f"scp {msg} {self.DATA_DIR}/{msg.split(':')[0]}-{file_name}",
                            shell=True,
                            executable='/bin/bash',
                            text=True,
                            capture_output=True,
                        )
                        logging.debug(f'[{get_time()}] [{address}] Copied {status}')
                        if status.returncode == 0:
                            logging.debug(f'[{get_time()}] [{address}] Sending OK')
                            connection.send('  OK'.encode(self.FORMAT))
                        else:
                            logging.debug(f'[{get_time()}] [{address}] Sending FAIL')
                            connection.send('FAIL'.encode(self.FORMAT))
                    else:
                        logging.debug(f'[{get_time()}] [{address}] Sending OK')
                        connection.send('  OK'.encode(self.FORMAT))

                except Exception as e:
                    logging.error(f'[{get_time()}] [{address}] ERROR {e}.')

        logging.debug(f'[{get_time()}] [{address}] Closing Connection.')
        connection.close()


    def start(self, server):
        server.listen()
        logging.debug(f'[{get_time()}] Listening at {server}.')

        try:
            while True:
                connection, address = server.accept()
                thread = threading.Thread(target=self.get_the_video, args=(connection, address))
                thread.start()
        except Exception as e:
            server.shutdown(socket.SHUT_RDWR)
            server.close()
            logging.debug(f'[{get_time()}] STOPPED.')

    def run(self):

        logging.basicConfig(filename=f'/home/alfred/Projects/Security_Cameras/Data/Test_Connection/logs/server_logs_{get_time()}.txt', level=logging.DEBUG) # ToDo filename move to __init__

        server = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(self.ADDR)

        logging.debug(f'[{get_time()}] Starting the server.')
        self.start(server)

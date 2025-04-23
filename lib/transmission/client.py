import os
import time
import socket
import logging
import datetime
from typing import Any, List
from lib.utils.timestamp import get_time



class Client:

    def __init__(self, params: Any, port: int = 7024):
        self.HEADER = 100
        self.PORT = port
        self.SERVER = socket.gethostbyname(params.server)
        self.ADDR = (self.SERVER, self.PORT)
        self.FORMAT = 'utf-8'
        self.DISCONNECT_MESSAGE = '!DISCONNECT'
        self.DATA_DIR = f'/home/{params.name}/RPI-Security/images'
        self.PREFIX = f'{params.name}@{socket.gethostbyname(params.hostname)}'

    @staticmethod
    def read_files(location: str) -> List[str]:
        return os.listdir(location)

    @staticmethod
    def argmax(items): # ToDo - move to utils. ToDo - rename to match specific argmax usage
        return max(enumerate(items), key=lambda x: x[1])[0]

    def get_all_but_last(self, videos_list: List[str]) -> List[str]: # ToDo - after argmax move, staticmethod can be used
        video_names = [x.rsplit('.', 1)[0] for x in videos_list]
        videos_timestamps = [time.mktime(datetime.datetime.strptime(x, '%Y-%m-%d_%H-%M-%S').timetuple()) for x in
                             video_names]
        max_video_index = self.argmax(videos_timestamps)

        print(max_video_index) # ToDo - add verbose to all prints
        print(videos_list[max_video_index])
        print(len(videos_list))
        del videos_list[max_video_index]
        return videos_list

    def send(self, msg, client):
        print(f'Sending {msg} to {client}')
        message = msg.encode(self.FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(self.FORMAT)
        padded_send_length = b' ' * (self.HEADER - len(send_length)) + send_length
        client.send(padded_send_length)
        client.send(message)

    def run(self):
        logging.basicConfig(filename=f'logs/client_logs_{get_time()}.txt', level=logging.DEBUG)

        counter = 0

        while True:

            logging.debug(f'[{get_time()}] Starting...')

            if len(os.listdir(self.DATA_DIR)) > 1:

                logging.debug(f'[{get_time()}] Files need to be send.')

                unsent = self.get_all_but_last(self.read_files(self.DATA_DIR))

                unsent.sort()

                logging.debug(f'[{get_time()}] Files to send {unsent}')

                if unsent:

                    logging.debug(f'[{get_time()}] Connecting to the {self.ADDR}.')

                    client = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
                    client.connect(self.ADDR)

                    logging.debug(f'[{get_time()}] Successfully connected to {self.ADDR}.')

                    for video_name in unsent:
                        counter += 1

                        logging.debug(f'[{get_time()}] [{counter}] Sending {video_name} to {self.ADDR}.')

                        video_full_path = os.path.join(self.DATA_DIR, video_name)

                        full_message = f'{self.PREFIX}:{video_full_path}'

                        self.send(full_message, client)
                        status = client.recv(4)
                        status = status.decode(self.FORMAT)

                        logging.debug(f'[{get_time()}] Server status {status}.')

                        print(f'Status {status}')
                        if status == '  OK':
                            logging.debug(f'[{get_time()}] Removing {video_full_path}...')
                            os.remove(video_full_path)
                            logging.debug(f'[{get_time()}] Removed {video_full_path}.')
                        elif status == 'FAIL':
                            print('Something is wrong')
                            logging.debug(f'[{get_time()}] Received FAIL message.')

                    self.send(self.DISCONNECT_MESSAGE, client)

            logging.debug(f'[{get_time()}] Sleeping for 30 min...')
            time.sleep(1)

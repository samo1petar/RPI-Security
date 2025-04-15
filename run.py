import random
import argparse

from lib.transmission.client import Client
from lib.transmission.server import Server


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--client', '-c', dest='client', type=str, default=None)
    parser.add_arguement('--port', '-p', dest='port', type=int, default=7024)
    parser.add_argument('--server', '-s', dest='server', action='store_true')

    args = parser.parse_args()

    assert args.server ^ args.client, f'This script needs to be called as a client or as a server, not both, not none.'

    if args.client:
        assert args.port > 1000, f'Port needs to be higher than 1000 to avoid collision with existing ports.'
        client = Client(args.client, args.port)
        client.run()
    elif args.server:
        server = Server(args.port)
        server.run()

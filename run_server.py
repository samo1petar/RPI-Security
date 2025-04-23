import argparse

from params import Server
from lib.transmission.server import Server


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--server', '-s', dest='server', action='store_true')
    parser.add_argument('--port', '-p', dest='port', type=int, default=7024)

    args = parser.parse_args()

    server = Server(Server(), args.port)
    server.run()

import argparse

from params import RPIZ1, RPIZ2
from lib.transmission.client import Client


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--client', '-c', dest='client', type=str, default=None)
    parser.add_argument('--port', '-p', dest='port', type=int, default=7024)

    args = parser.parse_args()

    params = {
        RPIZ1.name: RPIZ1(),
        RPIZ2.name: RPIZ2(),
    }

    # ToDo - port > 1000 ? what is appropriate port number ?
    assert args.port > 1000, f'Port needs to be higher than 1000 to avoid collision with existing ports.'
    assert args.client in params.keys()

    client = Client(params[args.client], args.port)
    client.run()

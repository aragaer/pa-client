#!/usr/bin/env python3
import argparse
import atexit
import getpass
import os
import socket
import time

import notify2
import yaml

from channels import PipeChannel, SocketChannel
from channels.poller import Poller


def cleanup(pipe):
    if os.path.exists(pipe):
        os.unlink(pipe)


def open_pipe(pipe, poller):
    f = os.open(pipe, os.O_RDONLY | os.O_NONBLOCK)
    poller.register(PipeChannel(f))


def connect(addr, poller):
    sock = socket.create_connection(addr)
    up = SocketChannel(sock)
    poller.register(up)
    up.write(getpass.getuser().encode()+b'\n')
    return up


def handle_pa_message(data):
    if data.startswith(b'Please enter your name> '):
        data = data[len('Please enter your name> '):]
        if not data:
            return
    if data:
        name, text = data.decode().strip().split('> ', 1)
        n = notify2.Notification(name.capitalize(), text)
        n.set_hint("transient", True)
        n.timeout = 2000
        n.show()
    else:
        n = notify2.Notification("PA", "Disconnected")
        n.timeout = 2000
        n.show()
        exit(0)


def main(config_file):
    notify2.init("pa-client")

    with open(config_file) as cfg:
        config = yaml.load(cfg)
    poller = Poller()

    addr = (config['server']['host'], config['server']['port'])
    pipe = config['client']['pipe']
    cleanup(pipe)
    os.mkfifo(pipe)
    open_pipe(pipe, poller)
    atexit.register(cleanup, pipe)
    atexit.register(poller.close_all)

    up = connect(addr, poller)

    try:
        while True:
            for data, channel in poller.poll():
                if channel == up:
                    handle_pa_message(data)
                else:
                    if data:
                        t, msg = data.split(b':')
                        if t == b'message':
                            if not msg.endswith(b'\n'):
                                msg += b'\n'
                            up.write(msg)
                        elif t == b'event':
                            msg = msg.strip()
                            if msg == b"presence" and up is None:
                                up = connect(addr, poller)
                            elif msg == b'gone' and up is not None:
                                poller.unregister(up)
                                up.close()
                                up = None
                    else:
                        open_pipe(pipe, poller)
    except KeyboardInterrupt:
        exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.yml")
    args = parser.parse_args()
    main(args.config)

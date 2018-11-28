#!/usr/bin/env python3
import argparse
import os
import subprocess


def naive_config_read(cfg):
    for line in cfg:
        key, val = line.strip().split(':')
        if key == 'pipe':
            return val.strip()
    else:
        print("Input pipe not found in config")
        exit(0)


def main(config_file):
    if not os.path.exists(config_file):
        os.chdir(os.path.dirname(__file__))
    with open(config_file) as cfg:
        input_pipe = naive_config_read(cfg)

    result = subprocess.run("dmenu",
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE)

    text = result.stdout.decode().strip()
    if not text:
        return

    print("message", text, sep=':')

    with open(input_pipe, 'w') as pipe:
        print("message", text, sep=':', file=pipe)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.yml")
    args = parser.parse_args()
    main(args.config)

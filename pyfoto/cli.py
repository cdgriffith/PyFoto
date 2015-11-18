#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging

from pyfoto.organizer import Organize

from pyfoto.config import get_stream_logger


def argument_parser():
    import argparse

    parser = argparse.ArgumentParser(description="PyFoto CLI")
    parser.add_argument("-d", "--directory", help="directory to ingest")
    parser.add_argument("-c", "--config-file", default="config.yaml",
                        help="Path to config file to use")
    parser.add_argument("--debug", default=False, action="store_true")
    parser.add_argument("-q", "--quiet", default=False, action="store_true")
    parser.add_argument("-t", "--tags", default=None, help="Tags to assign to all files")

    args = parser.parse_args()

    if args.debug and args.quiet:
        parser.print_help()
        raise Exception("Really? How can you be quiet and write debug?"
                        "Try just one of those options at a time.")

    return args


def main():

    args = argument_parser()

    root_logger = logging.getLogger("PyFoto")

    if args.quiet:
        root_logger.setLevel(logging.ERROR)
    else:
        root_logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    logger = get_stream_logger("cli")

    org = Organize(args.config_file)

    tags = tuple() if not args.tags else [x.strip().lower().replace(" ", "-") for x in args.tags.split(",") if x.strip()]

    if args.directory:
        for count in org.add_images(args.directory, tags=tags):
            logger.info("Processed: {0}".format(count))



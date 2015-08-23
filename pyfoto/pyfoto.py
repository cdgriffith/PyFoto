#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import logging

import bottle
import reusables


logger = logging.getLogger('pyfoto')
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)

app = bottle.Bottle()
root = os.path.abspath(os.path.dirname(__file__))
bottle.TEMPLATE_PATH.append(os.path.join(root, "templates"))

app.settings = {"directory": root,
                'structure': {},
                "base": ""}


def is_filetype(filename, filetype):
    for ext in reusables.common_exts[filetype]:
        if filename.endswith(ext):
            return True
    else:
        return False


def scan_dir(directory):
    structure = {}
    count = 0
    base_dir = directory.rsplit(os.sep, 1)[1]
    for base, dirs, files in os.walk(directory):
        dir_sub = os.path.join(base_dir, base[len(directory):]).strip(os.sep)
        logger.debug("Scanning {0}".format(base))
        for sub_dir in dirs:


        for file in files:
            if is_filetype(file, 'pictures'):
                count += 1
                if dir_sub in structure:
                    structure[dir_sub]['files'].append(file)
                else:
                    structure[dir_sub] = {"files": [file], "path": dir_sub.split(os.sep)}
        logger.debug("File count: {0}".format(count))

    return structure


@app.route("/static/<filename:path>")
def static_file(filename):
    return bottle.static_file(filename=filename,
                              root=os.path.join(root, "static"))


@app.route("/item/<filename:path>")
def static_file(filename):
    if filename.startswith(app.settings['base']):
        filename = filename[len(app.settings['base']) + 1:]
    return bottle.static_file(filename=filename,
                              root=app.settings['directory'])


@app.route("/folder", method="GET")
def get_folders():
    return {"folders": [{"path": k, "structure": v['path']} for k, v in app.settings['structure'].items()]}


@app.route("/folder/<name:path>", method="GET")
def get_folders(name):
    if reusables.win_based and "/" in name:
        name = name.replace("/", "\\")
    return app.settings['structure'][name]


@app.route("/", method="GET")
@bottle.view("index")
def index():
    return {}

def get_user_arguments():
    import argparse

    parser = argparse.ArgumentParser(description="PyCTF SERVER")
    parser.add_argument("-i", "--ip", default="localhost")
    parser.add_argument("-p", "--port", default=8080, type=int)
    parser.add_argument("-d", "--directory", default=".")

    return parser.parse_args()


def main():
    args = get_user_arguments()

    directory = os.path.abspath(args.directory)

    assert os.path.isdir(directory), "Supplied directory '{}' does not exist".format(directory)

    app.settings['directory'] = directory
    app.settings['structure'] = scan_dir(directory)
    app.settings['base'] = directory.rsplit(os.sep, 1)[1]

    bottle.run(app, host=args.ip, port=args.port, server="cherrypy")


if __name__ == '__main__':
    main()

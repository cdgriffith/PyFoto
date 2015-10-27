#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import absolute_import

import os
import logging

import bottle
from bottle.ext import sqlalchemy
import reusables

from organizer import Organize
from sqlalchemy import create_engine
from database import File, Tag, Series, Base
from config import get_config, default_config

logger = logging.getLogger('PyFoto')
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
logger.addHandler(sh)

app = bottle.Bottle()
root = os.path.abspath(os.path.dirname(__file__))
bottle.TEMPLATE_PATH.append(os.path.join(root, "templates"))

app.settings = {}

# noinspection PyUnresolvedReferences
@app.route("/static/<filename:path>")
def static_file(filename, db):
    return bottle.static_file(filename=filename,
                              root=os.path.join(root, "static"))


# noinspection PyUnresolvedReferences
@app.route("/item/<filename:path>")
def static_file(filename):
    if filename.startswith(app.settings.storage_directory):
        filename = filename[len(app.settings.storage_directory) + 1:]
    return bottle.static_file(filename=filename,
                              root=app.settings.storage_directory)


def prepare_file_items(query_return, settings):
    item_list = []
    for item in query_return:
        if item.type == "image":
            path = os.path.join(settings.image_dir, item.path)
        else:
            path = os.path.join(settings.video_dir, item.path)
        item_list.append({"id": item.id, "path": path, "filename": item.filename})

    return {"data": item_list}


@app.route("/next/<item_id>/<count>")
def next_items(item_id, count, db):
    items = db.query(File).order_by(File.id.asc()).filter(File.id > int(item_id)).limit(int(count))
    return prepare_file_items(items, app.settings)


@app.route("/prev/<item_id>/<count>")
def prev_items(item_id, count, db):
    items = db.query(File).order_by(File.id.desc()).filter(File.id < int(item_id)).limit(int(count))
    return prepare_file_items(items, app.settings)


@app.route("/", method="GET")
@bottle.view("index")
def index(db):
    return {}


def get_user_arguments():
    import argparse

    parser = argparse.ArgumentParser(description="PyFoto Server")
    parser.add_argument("-i", "--ip", default="localhost")
    parser.add_argument("-p", "--port", default=8080, type=int)
    parser.add_argument("-c", "--config_file", default="config.yaml")

    return parser.parse_args()


def main():
    args = get_user_arguments()

    app.settings = get_config(args.config_file)

    engine = create_engine(app.settings.connect_string, echo=True)

    plugin = sqlalchemy.Plugin(
    engine, # SQLAlchemy engine created with create_engine function.
    Base.metadata, # SQLAlchemy metadata, required only if create=True.
    keyword='db', # Keyword used to inject session database in a route (default 'db').
    create=True, # If it is true, execute `metadata.create_all(engine)` when plugin is applied (default False).
    commit=True, # If it is true, plugin commit changes after route is executed (default True).
    use_kwargs=False # If it is true and keyword is not defined, plugin uses **kwargs argument to inject session database (default False).
    )

    app.install(plugin)

    bottle.run(app, host=args.ip, port=args.port, server="cherrypy")


if __name__ == '__main__':
    main()

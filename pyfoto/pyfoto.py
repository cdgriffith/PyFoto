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
from sqlalchemy.orm.exc import NoResultFound
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
app.org = None


# noinspection PyUnresolvedReferences
@app.route("/static/<filename:path>")
def static_file(filename, db):
    return bottle.static_file(filename=filename,
                              root=os.path.join(root, "static"))


# noinspection PyUnresolvedReferences
@app.route("/item/<filename:path>")
def static_file(filename, db):
    if filename.startswith(app.settings.storage_directory):
        filename = filename[len(app.settings.storage_directory) + 1:]
    return bottle.static_file(filename,
                              root=os.path.abspath(app.settings.storage_directory))


@app.route("/file")
def get_items(db):
    options = bottle.request.query.decode()
    try:
        files = db.query(File).order_by(File.id.asc()).limit(options.get("count", 1000)).all()
    except NoResultFound:
        return {"data": []}
    return prepare_file_items(files, app.settings)


@app.route("/file/<file_id>")
def get_item(file_id, db):
    try:
        file = db.query(File).filter(File.id == int(file_id)).one()
    except NoResultFound:
        return bottle.abort(404, "file not found")
    return prepare_file_items([file], app.settings)


@app.route("/file/<file_id>/tag/<tag>", method="POST")
def add_tag_to_file(file_id, tag, db):
    options = bottle.request.query.decode()
    tag = add_tag(tag, options, db)
    try:
        file = db.query(File).filter(File.id == int(file_id)).one()
    except NoResultFound:
        return bottle.abort(404, "file not found")
    else:
        if not (tag in file.tags):
            file.tags.append(tag)
            db.commit()
    return {}


@app.route("/file/<file_id>/tag/<tag>", method="DELETE")
def remove_tag_from_file(file_id, tag, db):
    try:
        tag_item = db.query(Tag).filter(Tag.tag == tag).one()
        file_item = db.query(File).filter(File.id == file_id).one()
    except NoResultFound:
        return {"error": True}

    file_item.tags.remove(tag_item)
    return {"error": False}


@app.route("/file/ingest", method="POST")
def ingest_files(db):
    options = bottle.request.query.decode()
    if not options.get("directory") or not os.path.exists(options["directory"]):
        return {"error": True}

    if options.get("type") == "video":
        app.org.add_videos(options["directory"])
    else:
        app.org.add_images(options["directory"])
    return {"error": False}


@app.route("/tag")
def view_tags(db):
    tags = db.query(Tag).all()
    tag_list = []
    for tag in tags:
        tag_list.append(tag.tag)
    return {"data": tag_list}


@app.route("/tag/<tag>", method="POST")
def add_tag_route(tag, db):
    options = bottle.request.query.decode()
    add_tag(tag, options, db)
    return {}


def add_tag(tag, options, db):
    try:
        tag_item = db.query(Tag).filter(Tag.tag == tag).one()
    except NoResultFound:
        tag_item = Tag(tag=tag, description=options.get("description", ""))
        db.add(tag_item)
        db.commit()

    return tag_item


@app.route("/series/<series>", method="POST")
def add_series_route(series, db):
    options = bottle.request.query.decode()
    series = add_series(series, options, db)
    return {}


def add_series(series, options, db):
    try:
        series_item = db.query(Series).filter(Series.name == series).one()
    except NoResultFound:
        series_item = Series(name=series, description=options.get("description", ""),
                             source=options.get("source", ""),
                             url=options.get("url", ""))
        db.add(series_item)
        db.commit()
    return series_item


def prepare_file_items(query_return, settings):
    item_list = []
    for item in query_return:
        if item.type == "image":
            path = os.path.join(settings.image_dir, item.path)
        else:
            path = os.path.join(settings.video_dir, item.path)
        item_list.append({"id": item.id, "path": path, "filename": item.filename, "tags": [x.tag for x in item.tags],
                          "series": [x.name for x in item.series]})

    return {"data": item_list}


def filter_options(query, options, db):
    if options.get("tag"):
        tag = db.query(Tag).filter(Tag.tag == options['tag']).one()
        query = query.filter(File.tags.contains(tag))
    if options.get("series"):
        series = db.query(Series).filter(Series.name == options['series']).one()
        query = query.filter(File.series.contains(series))
    return query


def fun_search(search, db):
    query = db.query(File).filter(File.tags.any(Tag.tag.in_(search.split(" ")))).all()
    return query


@app.route("/next/<item_id>")
def next_items(item_id, db):
    options = bottle.request.query.decode()

    if options.get("search"):
        query = db.query(File).order_by(File.id.asc()).filter(File.id > int(item_id)).filter(File.tags.any(Tag.tag.in_(
            options["search"].split(" ")))).limit(1 if not options.get("count") else int(options['count'])).all()
    else:
        query = db.query(File).order_by(File.id.asc()).filter(File.id > int(item_id)).limit(1 if not options.get("count") else int(options['count'])).all()

    return prepare_file_items(query, app.settings)


@app.route("/prev/<item_id>")
def prev_items(item_id, db):
    options = bottle.request.query.decode()

    if options.get("search"):
        query = db.query(File).order_by(File.id.desc()).filter(File.id < int(item_id)).filter(File.tags.any(Tag.tag.in_(
            options["search"].split(" ")))).limit(1 if not options.get("count") else int(options['count'])).all()
    else:
        query = db.query(File).order_by(File.id.desc()).filter(File.id < int(item_id)).limit(1 if not options.get("count") else int(options['count'])).all()

    return prepare_file_items(query, app.settings)


@app.route("/search")
def search(db):
    options = bottle.request.query.decode()
    query = fun_search(options["search"],db)

    return prepare_file_items(query, app.settings)


@app.route("/", method="GET")
@bottle.view("index", template_settings=dict(syntax="<% %> % [[ ]]"))
def index():
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
        engine,
        Base.metadata,
        keyword='db',
        create=True,
        commit=True,
        use_kwargs=False
    )

    app.install(plugin)

    app.org = Organize(engine)

    bottle.run(app, host=args.ip, port=args.port, server="cherrypy")


if __name__ == '__main__':
    main()

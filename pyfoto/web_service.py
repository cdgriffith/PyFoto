#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import absolute_import

import os
import logging
import datetime
import json

import bottle
from bottle.ext import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound

from pyfoto.organizer import Organize
from pyfoto.database import File, Tag, Base
from pyfoto.config import get_config, get_stream_logger

logger = get_stream_logger('web_service')

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
                              root=os.path.abspath(
                                  app.settings.storage_directory))


@app.route("/file")
def get_items(db):
    options = bottle.request.query.decode()
    try:
        files = db.query(File).order_by(File.id.asc()).limit(
            options.get("count", 1000)).all()
    except NoResultFound:
        return {"data": []}
    return prepare_file_items(files, app.settings)


@app.route("/file/<file_id>")
def get_item(file_id, db):
    try:
        file = db.query(File).filter(File.id == int(file_id)).one()
    except NoResultFound:
        return bottle.abort(404, "file not found")
    results = prepare_file_items([file], app.settings)
    if not results:
        return bottle.abort(404, "file not found")

    return results


@app.route("/file/<file_id>", method="PUT")
def update_item(file_id, db):
    options = bottle.request.json

    try:
        file = db.query(File).filter(File.id == int(file_id)).one()
    except NoResultFound:
        return bottle.abort(404, "file not found")

    if "rating" in options:
        file.rating = options['rating']
    if "name" in options:
        file.name = options['name']
    if "description" in options:
        file.description = options['description']

    db.commit()
    return {"error": False}


@app.route("/file/<file_id>", method="DELETE")
def delete_item(file_id, db):
    try:
        file = db.query(File).filter(File.id == int(file_id)).one()
    except NoResultFound:
        return bottle.abort(404, "file not found")

    file.deleted = True
    db.commit()

    return {"error": False}


@app.route("/file/<file_id>/tag/<tag>", method="POST")
def add_tag_to_file(file_id, tag, db):
    tag = tag.strip().lower()
    if tag == "untagged":
        return {"error": True, "message": "The only way to add untagged, "
                                          "is remove all others."}

    options = bottle.request.query.decode()
    tag = add_tag(tag, options, db)
    try:
        file = db.query(File).filter(File.id == int(file_id)).one()
    except NoResultFound:
        return bottle.abort(404, "file not found")
    else:
        untagged = db.query(Tag).filter(Tag.tag == "untagged").one()
        if untagged in file.tags:
            file.tags.remove(untagged)

        if not (tag in file.tags):
            file.tags.append(tag)
            db.commit()
    return {}


@app.route("/file/<file_id>/tag/<tag>", method="DELETE")
def remove_tag_from_file(file_id, tag, db):
    tag = tag.strip().lower()
    if tag == "untagged":
        return {"error": True, "message": "The only way to remove untagged, "
                                          "is to add a new one."}
    try:
        tag_item = db.query(Tag).filter(Tag.tag == tag).one()
        file_item = db.query(File).filter(File.id == file_id).one()
    except NoResultFound:
        return {"error": True}

    file_item.tags.remove(tag_item)

    db.commit()
    return {"error": False}


@app.route("/tag")
def view_tags(db):
    tags = db.query(Tag).all()
    tag_list = []
    for tag in tags:
        tag_list.append({"tag": tag.tag, "private": tag.private})
    tag_list.sort(key=lambda x: x["tag"])
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


def prepare_file_items(query_return, settings):
    item_list = []
    for item in query_return:
        if item.deleted:
            continue

        name = item.filename if not item.name else item.name

        filename = name
        if not filename.lower().endswith(".{0}".format(item.extension)):
            filename = "{0}.{1}".format(name, item.extension)

        item_list.append({"id": item.id,
                          "path": item.path.replace("\\", "/"),
                          "name": name,
                          "filename": filename,
                          "width": item.width,
                          "height": item.height,
                          "tags": [{"tag": x.tag, "private": bool(x.private)} for x in item.tags],
                          "thumbnail": item.thumbnail.replace("\\", "/"),
                          "rating": item.rating})
    return {"data": item_list}


def filter_options(query, options, db):
    if options.get("tag"):
        tag = db.query(Tag).filter(Tag.tag == options['tag']).one()
        query = query.filter(File.tags.contains(tag))
    return query


def tag_search(term, db):
    if term == "untagged":
        query = db.query(File).filter(File.tags == None).limit(1000).all()
    else:
        query = db.query(File).filter(
            File.tags.any(Tag.tag.in_(term.split(" ")))).limit(1000).all()
    return query


def rating_search(rating, db, greater=True):
    return db.query(File).filter(File.rating >= rating if greater else File.rating <= rating).limit(1000).all()


def name_search(term, db):
    return db.query(File).filter(File.name == term).limit(1000).all()


def directional_item(item_id, db, forward=True, terms=None, count=1):

    query = db.query(File).order_by(File.id.asc() if forward else File.id.desc()).filter(
            File.deleted == 0).filter(File.id > int(item_id) if forward else File.id < int(item_id))

    if terms and "untagged" in terms:
        query = query.filter(File.tags == None)
    elif terms:
        query = query.filter(File.tags.any(Tag.tag.in_(terms.split(" "))))

    query = query.limit(count).all()

    return prepare_file_items(query, app.settings)


@app.route("/next/<item_id>")
def next_items(item_id, db):
    options = bottle.request.query.decode()

    return directional_item(item_id, db, True, options.get("search"),
                            int(options.get("count", 1)))


@app.route("/prev/<item_id>")
def prev_items(item_id, db):
    options = bottle.request.query.decode()

    return directional_item(item_id, db, False, options.get("search"),
                            int(options.get("count", 1)))


@app.route("/search")
def search_request(db):
    options = bottle.request.query.decode()
    search_type = options.get("search_type", "tag")

    if search_type == "rating":
        query = rating_search(int(options["search"]), db, greater=options.get("greater", True))
    elif search_type == "name":
        query = None
    else:
        query = tag_search(options["search"], db)

    return prepare_file_items(query, app.settings)


@app.route("/", method="GET")
@bottle.view("index", template_settings=dict(syntax="<% %> % [[ ]]"))
def index():
    return {}


@app.hook('after_request')
def log_after_request():
    logger.info('{ip} - - [{time}] "{method} {uri} {protocol}" {status}'.format(
        ip=bottle.request.environ.get('REMOTE_ADDR'),
        time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        method=bottle.request.environ.get('REQUEST_METHOD'),
        uri=bottle.request.environ.get('REQUEST_URI'),
        protocol=bottle.request.environ.get('SERVER_PROTOCOL'),
        status=bottle.response.status_code
    ))


def get_user_arguments():
    import argparse

    parser = argparse.ArgumentParser(description="PyFoto Server")
    parser.add_argument("-i", "--ip", default="localhost")
    parser.add_argument("-p", "--port", default=8080, type=int)
    parser.add_argument("-c", "--config_file", default="config.yaml")
    parser.add_argument("--debug", default=False, action="store_true")
    parser.add_argument("-q", "--quiet", default=False, action="store_true")

    args = parser.parse_args()

    if args.debug and args.quiet:
        parser.print_help()
        raise Exception("Really? How can you be quiet and write debug?"
                        "Try just one of those options at a time.")

    return args


def main():
    args = get_user_arguments()

    app.settings = get_config(args.config_file)

    root_logger = logging.getLogger("PyFoto")

    if args.quiet:
        root_logger.setLevel(logging.ERROR)
    else:
        root_logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    engine = create_engine(app.settings.connect_string, echo=False)

    plugin = sqlalchemy.Plugin(
        engine,
        Base.metadata,
        keyword='db',
        create=True,
        commit=True,
        use_kwargs=False
    )

    app.install(plugin)

    app.org = Organize(engine=engine)

    bottle.run(app, host=args.ip, port=args.port, server="cherrypy")


if __name__ == '__main__':
    main()

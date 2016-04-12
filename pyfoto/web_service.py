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
from sqlalchemy.sql import func, distinct

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


@app.route("/template/<template>")
def static_template(template, db):
    return bottle.static_file(filename=template,
                              root=os.path.join(root, "templates"))


# noinspection PyUnresolvedReferences
@app.route("/item/<filename:path>")
def static_image(filename, db):
    if filename.startswith(app.settings.storage_directory):
        filename = filename[len(app.settings.storage_directory) + 1:]
    return bottle.static_file(filename,
                              root=os.path.abspath(
                                  app.settings.storage_directory))


@app.route("/file")
def get_items(db):
    options = bottle.request.query.decode()
    count = int(options.get("count", 150))
    query = db.query(File).filter(File.deleted == False).filter(
            File.id >= int(options.get('start_at', 0))).order_by(
            File.id.asc())
    total = query.count()
    try:
        files = query.limit(count).all()
    except NoResultFound:
        return {"data": [], "total": 0}
    return prepare_file_items(files, app.settings, expected=count, total=total)


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

    file.last_updated = datetime.datetime.now()

    db.commit()
    return {"error": False}


@app.route("/file/<file_id>", method="DELETE")
def delete_item(file_id, db):
    try:
        file = db.query(File).filter(File.id == int(file_id)).one()
    except NoResultFound:
        return bottle.abort(404, "file not found")

    file.deleted = True
    file.last_updated = datetime.datetime.now()
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
        if not (tag in file.tags):
            file.tags.append(tag)
            file.last_updated = datetime.datetime.now()
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

    try:
        file_item.tags.remove(tag_item)
    except ValueError:
        return {"error": True, "message": "That tag isn't associated with anything yet"}

    file_item.last_updated = datetime.datetime.now()

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


@app.route("/tag/<tag>", method="DELETE")
def delete_tag_route(tag, db):
    return delete_tag(tag, db)


def delete_tag(tag, db):
        tag = tag.strip().lower()
        if tag == "untagged":
            return {"error": True, "message": "Can't do that dave"}
        try:
            tag_item = db.query(Tag).filter(Tag.tag == tag).one()
        except NoResultFound:
            return {"error": True, "message": "Tag {} does not exist".format(tag)}

        query = db.query(File).join(File.tags).filter(Tag.tag == tag).all()

        for file in query:
            file.tags.remove(tag_item)
            file.last_updated = datetime.datetime.now()

        db.query(Tag).filter(Tag.tag == tag).delete()

        return {"error": False}


@app.route("/tag/<tag>/count")
def count_tags(tag, db):
    if tag == "untagged":
        count = db.query(File).filter(File.deleted == 0).filter(File.tags == None).count()
    else:
        the_tag = db.query(Tag).filter(Tag.tag == tag).one()
        count = db.query(File).filter(File.deleted == 0).filter(File.tags.contains(the_tag)).count()
    return {"count": count}


def add_tag(tag, options, db):
    try:
        tag_item = db.query(Tag).filter(Tag.tag == tag).one()
    except NoResultFound:
        tag_item = Tag(tag=tag, description=options.get("description", ""))
        db.add(tag_item)
        db.commit()

    return tag_item


def prepare_file_items(query_return, settings, expected=None, total=None):
    item_list = []
    for item in query_return:
        if item.deleted:
            logger.warning("prepare_file_items got item {} which was deleted".format(item.id))
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

    return_data = {"data": item_list}
    if isinstance(expected, int) and expected > 0:
        return_data['expected'] = expected == len(item_list)
    if isinstance(total, int):
        return_data['total'] = total
    return return_data


def filter_options(query, options, db):
    if options.get("tag"):
        tag = db.query(Tag).filter(Tag.tag == options['tag']).one()
        query = query.filter(File.tags.contains(tag))
    return query


def directional_item(item_id, db, forward=True, tag=None, rating=0, count=1):

    query = db.query(File).order_by(File.id.asc() if forward else File.id.desc()).filter(
            File.deleted == 0)

    if tag and "untagged" in tag:
        query = query.filter(File.tags == None)
    elif tag:
        search_tags = tag.split(",")
        # Old Any search query = query.filter(File.tags.any(Tag.tag.in_(terms.split(" "))))
        query = query.join(File.tags).filter(Tag.tag.in_(search_tags)).group_by(File).having(
                func.count(distinct(Tag.id)) == len(search_tags))
    elif rating:
        query = query.filter(File.rating == rating)

    total = query.count()

    query = query.filter(File.id > int(item_id) if forward else File.id < int(item_id)).limit(count).all()

    return prepare_file_items(query, app.settings, expected=count, total=total)


@app.route("/next/<item_id>")
def next_items(item_id, db):
    options = bottle.request.query.decode()
    kwargs = {"count": int(options.get("count", 150))}
    if "search" in options:
        kwargs[options.get("search_type", "tag")] = options['search']
    return directional_item(item_id, db, True, **kwargs)


@app.route("/prev/<item_id>")
def prev_items(item_id, db):
    options = bottle.request.query.decode()
    kwargs = {"count": int(options.get("count", 150))}
    if "search" in options:
        kwargs[options.get("search_type", "tag")] = options['search']
    return directional_item(item_id, db, False, **kwargs)


@app.route("/search")
def search_request(db):
    options = bottle.request.query.decode()
    kwargs = {"count": int(options.get("count", 150)), options.get("search_type", "tag"): options['search']}
    return directional_item(int(options.get("start_at", 1)) - 1, db, **kwargs)


@app.route("/", method="GET")
def index():
    return bottle.redirect("/template/index.html", 302)


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

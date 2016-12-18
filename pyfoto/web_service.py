#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import absolute_import

import os
import logging
import datetime
import reusables
import random
from functools import wraps
import hashlib

import bottle
import reusables
from pbkdf2 import crypt
from bottle.ext import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import func, distinct

from pyfoto.organizer import Organize
from pyfoto.database import File, Tag, Base, Users, Auth, Album
from pyfoto.config import get_config, get_stream_logger

logger = get_stream_logger('web_service')

app = bottle.Bottle()
root = os.path.abspath(os.path.dirname(__file__))
bottle.TEMPLATE_PATH.append(os.path.join(root, "templates"))

app.settings = reusables.Namespace()
app.org = None


def auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = bottle.request.get_cookie('auth_token',
                                          secret=app.settings.get('cookie_key',
                                                                  '1234'))
        if not token:
            logger.debug("No token provided for request")
            return {"error": True, "message": "Access Denied"}
        engine = create_engine(app.settings.connect_string, echo=False)
        session = sessionmaker(bind=engine)
        db = session()
        try:
            # Last arg should be 'db'
            auth_token = db.query(Auth).filter(Auth.token == token).one()
        except NoResultFound:
            logger.debug("No corresponding auth token found")
            return {"error": True, "message": "Access Denied"}
        else:
            if auth_token.expires <= datetime.datetime.now():
                logger.debug("Token expired")
                return {"error": True, "message": "Access Denied"}
            else:
                kwargs['db'] = db
                return func(*args, **kwargs)
        finally:
            db.close()
    return wrapper


def calc_pass(passwd, stored_pass=None):
    return crypt(passwd, stored_pass, iterations=app.settings.pass_iterations)


def gen_token(username):
    return hashlib.sha256('{}-{}-{}'.format(username,
                                            datetime.datetime.now().isoformat(),
                                            random.randint(0, 9)
                                            ).encode("utf-8")).hexdigest()


@app.route("/auth/login", method="POST")
def login(db):
    options = bottle.request.json

    if "username" not in options or "password" not in options:
        return {"error": True,
                "message": "Must provide all required login fields"}

    try:
        user = db.query(Users).filter(Users.username == options['username']).one()
    except NoResultFound:
        return {'error': True, "message": "Auth failed"}
    else:
        if user.pass_hash == calc_pass(options['password'], user.pass_hash):
            token = gen_token(user.username)
            new_auth = Auth(user_id=user.id, token=token)
            db.add(new_auth)
            db.commit()
            bottle.response.set_cookie('auth_token', token, secret=app.settings.get('cookie_key', '1234'), path="/")
            return {'error': False, 'token': token}

    return {'error': True, "message": "Auth failed"}


@app.route("/auth/logout", method="POST")
def logout(db):
    token = bottle.request.get_cookie('auth_token', secret=app.settings.get('cookie_key', '1234'))
    if token:
        logger.info("Logout successful")
        db.query(Auth).filter(Auth.token == token).delete()
    else:
        logger.warning("Couldn't get cookie for logout")
    return {}


def add_user(username, password, db):
    new_user = Users(username=username, pass_hash=calc_pass(password))
    db.add(new_user)
    db.commit()


@app.route("/test_route")
@auth
def test_route(db):
    return {"here": True}


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
@auth
def static_image(filename, db):
    if filename.startswith(app.settings.storage_directory):
        filename = filename[len(app.settings.storage_directory) + 1:]
    return bottle.static_file(filename,
                              root=os.path.abspath(
                                  app.settings.storage_directory))


@app.route("/file")
@auth
def get_items(db):
    options = bottle.request.query.decode()
    count = int(options.get("count", 1000))
    start_at = int(options.get('start_at')) if options.get('start_at') else 0
    query = db.query(File).filter(File.deleted == False).filter(
            File.id >= start_at).order_by(File.id.asc())
    total = query.count()
    try:
        files = query.limit(count).all()
    except NoResultFound:
        return {"data": [], "total": 0}
    return prepare_file_items(files, app.settings, expected=count, total=total)


@app.route("/file/<file_id>")
@auth
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
@auth
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
@auth
def delete_item(file_id, db):
    try:
        file = db.query(File).filter(File.id == int(file_id)).one()
    except NoResultFound:
        return bottle.abort(404, "file not found")

    file.deleted = True
    file.last_updated = datetime.datetime.now()
    db.commit()

    return {"error": False, "file_id": int(file_id)}


@app.route("/file/<file_id>/tag/<tag>", method="POST")
@auth
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
@auth
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
@auth
def view_tags(db):
    tags = db.query(Tag).all()
    tag_list = [{"tag": tag.tag, "private": tag.private} for tag in tags]
    tag_list.sort(key=lambda x: x["tag"])
    return {"data": tag_list}


@app.route("/tag/<tag>", method="POST")
@auth
def add_tag_route(tag, db):
    options = bottle.request.query.decode()
    add_tag(tag, options, db)
    return {}


@app.route("/tag/<tag>", method="DELETE")
@auth
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
@auth
def count_tags(tag, db):
    if tag == "untagged":
        count = db.query(File).filter(File.deleted == 0).filter(File.tags == None).count()
    else:
        the_tag = db.query(Tag).filter(Tag.tag == tag).one()
        count = db.query(File).filter(File.deleted == 0).filter(File.tags.contains(the_tag)).count()
    return {"count": count}


@app.route("/tag/<tag>/merge")
@auth
def merge_tags(tag, db):
    if tag == "untagged":
        return {"error": True, "message": "Can't do that dave"}
    items = bottle.request.json


def add_tag(tag, options, db):
    try:
        tag_item = db.query(Tag).filter(Tag.tag == tag).one()
    except NoResultFound:
        tag_item = Tag(tag=tag, description=options.get("description", ""))
        db.add(tag_item)
        db.commit()

    return tag_item


@app.route("/album/<album>")
@auth
def get_album(album, db):
    # TODO undtested, need to list files?
    return db.query(Album).filter(Album.name == album).one()

@app.route("/album/<album>/file/<file>", method="POST")
@auth
def add_file_to_album(album, file, db):
    #TODO
    pass

@app.route("/album/<album>/file/<file>", method="DELETE")
@auth
def remove_file_to_album(album, file, db):
    #TODO
    pass

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
                          "extension": item.extension,
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


def directional_item(item_id, db, forward=True, tag=None, name=None, rating=0, count=1):

    query = db.query(File).order_by(File.id.asc() if forward else File.id.desc()).filter(
            File.deleted == 0)

    if name:
        query = query.filter(File.filename.contains(name))
    elif tag and "untagged" in tag:
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
@auth
def next_items(item_id, db):
    options = bottle.request.query.decode()
    kwargs = {"count": int(options.get("count", 1000))}
    if "search" in options:
        kwargs[options.get("search_type", "name")] = options['search']
    return directional_item(item_id, db, True, **kwargs)


@app.route("/prev/<item_id>")
@auth
def prev_items(item_id, db):
    options = bottle.request.query.decode()
    kwargs = {"count": int(options.get("count", 1000))}
    if "search" in options:
        kwargs[options.get("search_type", "name")] = options['search']
    return directional_item(item_id, db, False, **kwargs)


@app.route("/search")
@auth
def search_request(db):
    options = bottle.request.query.decode()
    kwargs = {"count": int(options.get("count", 1000)), options.get("search_type", "name"): options['search']}
    return directional_item(int(options.get("start_at", 1)) - 1, db, **kwargs)


@app.route("/", method="GET")
def index():
    return bottle.redirect("/template/index.html", 302)


@app.route("/login", method="GET")
def index():
    return bottle.redirect("/template/login.html", 302)


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


def first_time_setup(engine, settings):
    session = sessionmaker(bind=engine)
    db = session()

    try:
        db.query(Users).filter(Users.username == 'admin').one()
    except NoResultFound:
        add_user('admin', settings.default_admin_pass, db)
        logger.info("Admin default password set to: {}, please update".format(
            settings.default_admin_pass))
    finally:
        db.close()


def main():
    args = get_user_arguments()

    app.settings = get_config(args.config_file)

    root_logger = logging.getLogger("PyFoto")

    if args.quiet:
        root_logger.setLevel(logging.ERROR)
    else:
        root_logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    engine = create_engine(app.settings.connect_string, echo=False)

    Base.metadata.create_all(engine)

    plugin = sqlalchemy.Plugin(
        engine,
        Base.metadata,
        keyword='db',
        create=True,
        commit=True,
        use_kwargs=False
    )

    first_time_setup(engine, app.settings)

    app.install(plugin)

    app.org = Organize(engine=engine)

    bottle.run(app, host=args.ip, port=args.port, server="cherrypy")


if __name__ == '__main__':
    main()

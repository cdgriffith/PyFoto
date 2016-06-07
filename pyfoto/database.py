#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Column, Integer, String, Table, ForeignKey,
                        PrimaryKeyConstraint, Boolean, DateTime)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


Base = declarative_base()

tag_ass_table = Table('tag_association',
                      Base.metadata,
                      Column('file_id', Integer, ForeignKey('files.id')),
                      Column('tag_id', Integer, ForeignKey('tags.id')),
                      PrimaryKeyConstraint('file_id', 'tag_id'))


class File(Base):

    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    path = Column(String(512))
    sha256 = Column(String(64))
    extension = Column(String(10))
    size = Column(Integer)
    filename = Column(String(256))
    thumbnail = Column(String(512))
    deleted = Column(Boolean, default=False)
    name = Column(String(512), default="")
    width = Column(Integer)
    height = Column(Integer)
    description = Column(String(256), default="")
    rating = Column(Integer, default=0)
    ingested_date = Column(DateTime, default=func.now())
    last_updated = Column(DateTime, default=func.now())

    tags = relationship("Tag", secondary=tag_ass_table)


class Tag(Base):

    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    tag = Column(String(64))
    description = Column(String(256), default="")
    private = Column(Boolean, default=False)


class Users(Base):

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(64))
    pass_hash = Column(String(64))
    last_access = Column(DateTime, default=func.now())


class Auth(Base):

    __tablename__ = 'auth'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    token = Column(String(128))
    expires = Column(DateTime, default=(datetime.datetime.utcnow() + datetime.timedelta(hours=12)))



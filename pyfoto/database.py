#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Column, Integer, String, Table, ForeignKey,
                        PrimaryKeyConstraint, Boolean)
from sqlalchemy.orm import relationship

Base = declarative_base()

tag_association_table = Table('tag_association', Base.metadata,
                              Column('file_id', Integer,
                                     ForeignKey('files.id')),
                              Column('tag_id', Integer,
                                     ForeignKey('tags.id')),
                              PrimaryKeyConstraint('file_id', 'tag_id'))


class File(Base):

    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    path = Column(String)
    sha256 = Column(String)
    extension = Column(String)
    size = Column(Integer)
    type = Column(String)
    filename = Column(String)
    thumbnail = Column(String)
    deleted = Column(Boolean, default=False)
    name = Column(String, default="")
    description = Column(String, default="")
    rating = Column(Integer, default=0)

    tags = relationship("Tag", secondary=tag_association_table)


class Tag(Base):

    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    tag = Column(String)
    description = Column(String, default="")
    private = Column(Boolean, default=False)

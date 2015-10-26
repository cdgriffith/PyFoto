#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()

tag_association_table = Table('tag_association', Base.metadata,
                              Column('file_id', Integer, ForeignKey('files.id')),
                              Column('tag_id', Integer, ForeignKey('tags.id')))


class File(Base):

    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    path = Column(String)
    sha256 = Column(String)
    extension = Column(String)
    size = Column(Integer)

    tags = relationship("Tags", secondary=tag_association_table)


class Tags(Base):

    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    tag = Column(String)
    description = Column(String)



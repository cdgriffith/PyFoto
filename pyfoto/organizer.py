#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import print_function, absolute_import

import os
import logging
import shutil

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
import reusables

from database import File, Tag, Base, Series
from config import get_config, save_config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("PyFoto")


class Organize:

    def __init__(self, engine=None):
        self.config = get_config()

        if not engine:
            engine = create_engine(self.config.connect_string, echo=True)
        Base.metadata.create_all(engine, checkfirst=True)
        self.session = sessionmaker(bind=engine)()

        self.ensure_exists(self.config.video_dir)
        self.ensure_exists(self.config.image_dir)
        self.save_config()

    @staticmethod
    def ensure_exists(path):
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def file_extension(file):
        ext = file.rsplit(".", 1)[1].lower()
        if ext == "jpeg":
            ext = "jpg"
        if ext == "tiff":
            ext = "tif"
        return ext

    def file_info(self, file):
        sha256 = reusables.file_hash(file, "sha256")
        ext = self.file_extension(file)
        size = os.path.getsize(file)

        return sha256, ext, size

    def already_ingested(self, sha256):
        """Determine if an item has already been ingested by comparing it to existing SHA256s"""
        if self.session.query(File).filter(File.sha256 == sha256).all():
            return True
        return False

    def ingest(self, file, ingest_path, sha256, file_type, series=""):
        """Copy a file to the new location and verify it was copied completely with the hash"""

        full_path = os.path.join(self.config.image_dir if file_type == "image" else self.config.video_dir, ingest_path)

        self.ensure_exists(os.path.dirname(full_path))

        if os.path.exists(full_path):
            raise Exception("File already exists and should not, halting.")

        shutil.copy(file, full_path)
        new_sha256, ext, size = self.file_info(full_path)

        if new_sha256 == sha256:
            if series:
                try:
                    sql_series = self.session.query(Series).filter(Series.name == series).one()
                except NoResultFound:
                    sql_series = Series(name=series)
                new_file = File(path=ingest_path, sha256=sha256, extension=ext, size=size, type=file_type,
                                filename=os.path.basename(file), series=[sql_series])
            else:
                new_file = File(path=ingest_path, sha256=sha256, extension=ext, size=size, type=file_type,
                                filename=os.path.basename(file))
            self.session.add(new_file)
            if self.config.remove_source:
                os.unlink(file)
        else:
            logger.error("File {0} did not copy correctly!".format(file))
            os.unlink(full_path)

    def save_config(self):
        save_config(self.config.to_dict())

    def add_images(self, directory, series=""):
        """Go through a directory for all image files and ingest them"""
        for file in reusables.find_all_files_generator(directory, ext=reusables.exts.pictures):
            sha256, ext, size = self.file_info(file)
            if not self.config.ignore_duplicates and self.already_ingested(sha256):
                logger.warning("file {0} already ingested".format(file))
                continue

            self.config.image_file_inc += 1
            if self.config.image_file_inc > self.config.folder_limit:
                self.config.image_file_inc = 0
                self.config.image_dir_inc += 1
                self.session.commit()
                self.save_config()

            ingest_folder = self.config.dir_names.format(increment=self.config.image_dir_inc)

            ingest_path = os.path.join(ingest_folder,
                                       self.config.image_names.format(increment=self.config.image_file_inc,
                                                                      ext=ext,
                                                                      hash=sha256,
                                                                      size=size))

            try:
                self.ingest(file, ingest_path, sha256, file_type="image", series=series)
            except Exception as err:
                self.save_config()
                self.session.commit()
                raise err

        self.session.commit()
        self.save_config()


    def add_videos(self, directory, series=""):
        pass

    def ingest_items(self, directory, item_type="images", series=""):
        self.q.put((directory, item_type, series))

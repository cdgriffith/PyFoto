#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import print_function, absolute_import

import os
import logging
import shutil

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import yaml
import reusables

from .database import File, Tags, Base
from .config import get_config, save_config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("PyFoto")



class Organize:

    def __init__(self, connect_string="sqlite:///pyfoto.sqlite"):
        engine = create_engine(connect_string, echo=True)
        Base.metadata.create_all(engine, checkfirst=True)
        self.session = sessionmaker(bind=engine)()

        self.config = get_config()

        self.video_dir = (self.config['storage_directory'] if not self.config.get('video_sub_dir') else
                          os.path.join(self.config['storage_directory'], self.config['video_sub_dir']))

        self.image_dir = (self.config['storage_directory'] if not self.config.get('image_sub_dir') else
                          os.path.join(self.config['storage_directory'], self.config['image_sub_dir']))

        self.ensure_exists(self.video_dir)
        self.ensure_exists(self.image_dir)
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
        if self.session.query(File).filter(File.sha256 == sha256).all():
            return True
        return False

    def ingest(self, file, ingest_path, sha256, file_type, series=""):
        """Copy a file to the new location and verify it was copied completely with the hash"""

        full_path = os.path.join(self.image_dir if file_type == "image" else self.video_dir, ingest_path)

        self.ensure_exists(os.path.dirname(full_path))

        if os.path.exists(full_path):
            raise Exception("File already exists and should not, halting.")

        shutil.copy(file, full_path)
        new_sha256, ext, size = self.file_info(full_path)

        if new_sha256 == sha256:
            new_file = File(path=ingest_path, sha256=sha256, extension=ext, size=size, type=file_type,
                            filename=os.path.basename(file), series=series)
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

            self.ingest(file, ingest_path, sha256, file_type="image", series=series)
        self.session.commit()
        self.save_config()


    def add_videos(self, directory):
        pass

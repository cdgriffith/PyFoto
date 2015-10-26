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

from .database import File, Tags

logger = logging.getLogger(__name__)


def get_config(config_file="config.yaml"):
    with open(config_file) as f:
        return yaml.load(f)


class Organize:

    images = reusables.exts.pictures
    videos = reusables.exts.video
    # TODO add {date}, {time}, {type}, {hash}, {size}
    dir_names = "{increment}"
    image_names = "{increment}.{ext}"
    video_names = "{increment}.{ext}"
    remove_source = False
    folder_limit = 1000
    ignore_duplicates = False


    def __init__(self, config_file="config.yaml"):
        self.config = get_config(config_file)
        if not os.path.exists(self.config['storage_directory']):
            os.makedirs(self.config['storage_directory'])

        self.video_dir = (self.config['storage_directory'] if not self.config.get('video_dir') else
                          os.path.join(self.config['storage_directory'], self.config['video_dir']))
        self.image_dir = (self.config['storage_directory'] if not self.config.get('image_dir') else
                          os.path.join(self.config['storage_directory'], self.config['image_dir']))
        self.current_video_dir_int = 1
        self.current_image_dir_int = 1
        self.current_video_file_inc = 1
        self.current_image_file_inc = 1
        engine = create_engine('sqlite:///:memory:', echo=True)
        session = sessionmaker(bind=engine)
        self.session = session()

    @staticmethod
    def file_extension(file):
        return file.rsplit(".", 1)[1]

    def file_info(self, file):
        sha256 = reusables.file_hash(file, "sha256")
        ext = self.file_extension(file)
        size = os.path.getsize(file)

        return sha256, ext, size

    def file_hash(self, file):
        return "hash"

    def already_ingested(self, file):
        return False

    @staticmethod
    def verify(file, ingest_path):
        if reusables.file_hash(file, "sha256") == reusables.file_hash(ingest_path, "sha256"):
            return True
        return False

    def ingest(self, file, ingest_path):
        shutil.copy(file, ingest_path)
        if self.verify(file, ingest_path):
            sha256, ext, size = self.file_info(ingest_path)
            new_file = File(path=ingest_path, sha256=sha256, extension=ext, size=size)
            self.session.add(new_file)
            self.session.commit()
            if self.remove_source:
                os.unlink(file)
        else:
            logger.error("File {0} did not copy correctly!".format(file))
            os.unlink(ingest_path)

    def add_images(self, directory):

        for file in reusables.find_all_files_generator(directory, ext=self.images):
            if not self.ignore_duplicates and self.already_ingested(file):
                logger.warning("file already ingested")
                continue
            self.current_image_file_inc += 1
            if self.current_image_file_inc > self.folder_limit:
                self.current_image_file_inc = 0
                self.current_image_dir_int += 1

            self.ingest(file, os.path.join(self.image_dir,
                self.dir_names.format(increment=self.current_image_dir_int),
                self.image_dir.format(increment=self.current_image_file_inc, ext=self.file_extension(file))))

    def add_videos(self, directory):
        pass


#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import print_function, absolute_import

import os
import shutil

from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
import reusables

from pyfoto.database import File, Tag, Base
from pyfoto.config import get_config, save_config, get_stream_logger

logger = get_stream_logger("organizer")


class Organize:

    def __init__(self, config_file: str="config.yaml", engine=None):

        self.config = get_config(config_file)

        if not engine:
            engine = create_engine(self.config.connect_string)
        Base.metadata.create_all(engine, checkfirst=True)
        self.session = sessionmaker(bind=engine)()

        self.ensure_exists(self.config.storage_directory)
        self.save_config()

    @staticmethod
    def ensure_exists(directory: str) -> None:
        """
        If a specified path does not exist, create it.

        :param directory: Path to make sure exists.
        :return:
        """

        if directory and not os.path.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def file_extension(file: str) -> str:
        """
        Returns the extension of the file.

        :param file: Path to file as string.
        :return:
        """

        ext = file.rsplit(".", 1)[1].lower()
        if ext == "jpeg":
            ext = "jpg"
        if ext == "tiff":
            ext = "tif"
        return ext

    def file_info(self, file: str) -> tuple:
        """
        Returns file information.

        :param file: Path to file as string.
        :return:
        """

        sha256 = reusables.file_hash(file, "sha256")
        ext = self.file_extension(file)
        size = os.path.getsize(file)

        return sha256, ext, size

    def already_ingested(self, sha256: str) -> bool:
        """
        Determine if an item has already been ingested by
        comparing it to existing SHA256s.

        :param sha256:
        :return:
        """

        if self.session.query(File).filter(File.sha256 == sha256).all():
            return True
        return False

    def tag_strings_to_tags(self, tags: tuple) -> list:
        """
        Take a list of strings that represent tags
        and return SQLAlchemy objects.

        :param tags: list of string tags.
        :return: list of SQLAlchemy objects.
        """

        tags = list(tags)

        if not tags:
            tags.append("untagged")

        add_tags = []
        for tag in tags:
            try:
                add_tag = self.session.query(Tag).filter(Tag.tag == tag).one()
            except NoResultFound:
                add_tag = Tag(tag=tag)
                self.session.add(add_tag)
            if add_tag in add_tags:
                continue
            add_tags.append(add_tag)

        return add_tags

    def ingest(self, file: str, ingest_path: str, sha256: str,
               file_type: str="image", tags: tuple=()) -> None:
        """
        Copy a file to the new location and verify it was
        copied completely with the hash. Also create a thumbnail of the item.

        :param file:
        :param ingest_path:
        :param sha256:
        :param file_type:
        :param tags:
        :return:
        """

        full_path = os.path.join(self.config.storage_directory, ingest_path)

        self.ensure_exists(os.path.dirname(full_path))

        if os.path.exists(full_path):
            raise Exception("File already exists and should not, halting. {0}".format(full_path))

        shutil.copy(file, full_path)
        new_sha256, ext, size = self.file_info(full_path)

        if new_sha256 != sha256:
            logger.error("File {0} did not copy correctly!".format(file))
            os.unlink(full_path)
            return

        thumb_path = os.path.join("thumbs", ingest_path.rsplit(".")[0] + ".jpg")
        thumb_dir = os.path.join(self.config.storage_directory, thumb_path)

        try:
            self.create_thumbnail(full_path, thumb_dir)
        except Exception as err:
            logger.exception("Count not create thumbnail for {0}, will "
                             "redirect to main image. "
                             "Error: {1}".format(file, err))
            thumb_path = ingest_path

        new_file = File(path=ingest_path, sha256=sha256, extension=ext,
                        size=size, type=file_type,
                        filename=os.path.basename(file),
                        thumbnail=thumb_path,
                        tags=self.tag_strings_to_tags(tags))

        self.session.add(new_file)
        if self.config.remove_source:
            os.unlink(file)

    def save_config(self) -> None:
        """
        Convert the config to dict and write it out to the YAML file.

        :return:
        """

        save_config(self.config.to_dict())

    def add_images(self, directory: str, tags: tuple=()):
        """
        Go through a directory for all image files and ingest them.

        :param directory:
        :param tags:
        :return:
        """

        total = 0
        # I don't use enumerate because I have to return the number at the end
        for file in reusables.find_all_files_generator(
                directory, ext=reusables.exts.pictures):
            total += 1
            if total % 5.0 == 0.0:
                yield total

            sha256, ext, size = self.file_info(file)
            if (not self.config.ignore_duplicates and
                    self.already_ingested(sha256)):
                logger.warning("file {0} already ingested".format(file))
                continue

            self.config.file_inc += 1
            if self.config.file_inc > self.config.folder_limit:
                self.config.file_inc = 0
                self.config.dir_inc += 1
                self.session.commit()
                self.save_config()

            ingest_folder = self.config.dir_names.format(
                                increment=self.config.dir_inc)

            ingest_path = os.path.join(ingest_folder,
                                       self.config.file_names.format(
                                           increment=self.config.file_inc,
                                           ext=ext,
                                           hash=sha256,
                                           size=size))

            try:
                self.ingest(file, ingest_path, sha256,
                            file_type="image", tags=tags)
            except Exception as err:
                self.save_config()
                self.session.commit()
                raise err

        self.session.commit()
        self.save_config()
        yield total

    def create_thumbnail(self, file: str, out_path: str,
                         width: int=250, height: int=250) -> None:
        """
        Create a thumbnail with Pillow then save it to the out_path.

        :param file:
        :param out_path:
        :param width:
        :param height:
        :return:
        """

        self.ensure_exists(os.path.dirname(out_path))
        im = Image.open(file)
        im.thumbnail((width, height))
        try:
            im.save(out_path, "JPEG")
        except OSError:
            im.convert('RGB').save(out_path, "JPEG")




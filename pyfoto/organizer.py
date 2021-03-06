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

    def _tag_strings_to_tags(self, tags: tuple) -> list:
        """
        Take a list of strings that represent tags
        and return SQLAlchemy objects.

        :param tags: list of string tags.
        :return: list of SQLAlchemy objects.
        """

        tags = list(tags)

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

    def _ingest(self, file: str, ingest_path: str, sha256: str,
                tags: tuple=()) -> None:
        """
        Copy a file to the new location and verify it was
        copied completely with the hash. Also create a thumbnail of the item.

        :param file:
        :param ingest_path:
        :param sha256:
        :param tags:
        :return:
        """

        full_path = os.path.join(self.config.storage_directory, ingest_path)

        self.ensure_exists(os.path.dirname(full_path))

        if os.path.exists(full_path):
            raise Exception("File already exists and should not, halting. "
                            "{0}".format(full_path))

        shutil.copy(file, full_path)
        new_sha256, ext, size = self.file_info(full_path)

        if new_sha256 != sha256:
            logger.error("File {0} did not copy correctly!".format(file))
            os.unlink(full_path)
            return

        thumb_path = os.path.join("thumbs", ingest_path.rsplit(".")[0] + ".jpg")
        thumb_dir = os.path.join(self.config.storage_directory, thumb_path)

        try:
            width, height = self.create_thumbnail(full_path, thumb_dir)
        except Exception as err:
            logger.exception("Count not create thumbnail for {0}, will "
                             "redirect to main image. "
                             "Error: {1}".format(file, err))
            thumb_path = ingest_path
            width, height = 0, 0

        new_file = File(path=ingest_path, sha256=sha256, extension=ext,
                        size=size, filename=os.path.basename(file),
                        thumbnail=thumb_path, width=width, height=height,
                        tags=self._tag_strings_to_tags(tags))

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

        :param breaker:
        :param directory:
        :param tags:
        :return:
        """

        total = 0
        # I don't use enumerate because I have to return the number at the end
        for file in reusables.find_all_files_generator(
                directory, ext=reusables.exts.pictures):
            total += 1
            if total % 20 == 0.0:
                logger.info("Ingested {0} images so far.".format(total))

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
                self._ingest(file, ingest_path, sha256, tags=tags)
            except Exception as err:
                self.save_config()
                self.session.commit()
                raise err

        self.session.commit()
        self.save_config()
        return total

    def create_thumbnail(self, file: str, out_path: str,
                         width: int=250, height: int=250) -> tuple:
        """
        Create a thumbnail with Pillow then save it to the out_path. It will
        return the original image's width and height.

        :param file:
        :param out_path:
        :param width:
        :param height:
        :return:
        """

        self.ensure_exists(os.path.dirname(out_path))
        im = Image.open(file)
        org_width, org_height = im.size
        im.thumbnail((width, height))
        try:
            im.save(out_path, "JPEG")
        except OSError:
            im.convert('RGB').save(out_path, "JPEG")
        return org_width, org_height

    def pull_deleted(self, move_dir=None):
        if not move_dir:
            move_dir = os.path.join(self.config.storage_directory, os.path.pardir, "pyfoto_deleted")
        self.ensure_exists(move_dir)
        all_deleted = self.session.query(File).filter(File.deleted == 1).filter(File.path != None).all()
        logger.info("{} deleted files about to be processed".format(len(all_deleted)))
        for item in all_deleted:
            if item.path and os.path.exists(os.path.join(self.config.storage_directory, item.path)):
                shutil.move(os.path.join(self.config.storage_directory, item.path), os.path.join(move_dir, "{}.{}".format(item.sha256, item.extension)))
                item.path = None
                item.tags = []
        self.session.commit()

    def pull_tag(self, tag="edit", move_dir=None, delete=True):
        if not move_dir:
            move_dir = os.path.join(self.config.storage_directory, os.path.pardir, "pyfoto_{}".format(tag))
        self.ensure_exists(move_dir)
        all_edits = self.session.query(File).filter(File.tags.any(Tag.tag == tag)).all()
        logger.info("{} edited files about to be processed".format(len(all_edits)))
        for item in all_edits:
            if item.path and os.path.exists(os.path.join(self.config.storage_directory, item.path)):
                shutil.move(os.path.join(self.config.storage_directory, item.path), os.path.join(move_dir, "{}.{}".format(item.sha256, item.extension)))
                if delete:
                    item.deleted = 1
                    item.tags = []
                    item.path = None
        self.session.commit()

#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from .database import Config, Base
import reusables

default_config = dict(
    storage_directory="storage",
    images=reusables.exts.pictures,
    videos=reusables.exts.video,
    # TODO add {date}, {time}, {type}, {hash}, {size}
    dir_names="{increment}",
    image_names="{increment}.{ext}",
    video_names="{increment}.{ext}",
    remove_source=False,
    folder_limit=1000,
    ignore_duplicates=False,
    video_dir_inc=1,
    image_dir_inc=1,
    video_file_inc=1,
    image_file_inc=1,
    sql_type="sqlite",
    sqlite_file="pyfoto.sqlite",
    video_sub_dir="videos",
    image_sub_dir="images"
)


def get_config():
    return reusables.Namespace(**default_config)

#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import logging

import json
import reusables

logger = logging.getLogger("PyFoto")

default_config = dict(
    storage_directory="storage",
    # TODO add {date}, {time}, {type}, {hash}, {size}
    dir_names="{increment}",
    image_names="{increment}.{ext}",
    video_names="{increment}.{ext}",
    remove_source=False,
    folder_limit=1000,
    ignore_duplicates=False,
    video_dir_inc=1,
    image_dir_inc=1,
    video_file_inc=0,
    image_file_inc=0,
    video_sub_dir="videos",
    image_sub_dir="images"
)


def get_config(config_file="config.json"):
    config = default_config.copy()

    if os.path.exists(config_file):
        with open(config_file) as f:
            config.update(json.load(f))
    logger.info("Loaded config")
    logger.debug("Config - {0}".format(config))

    return reusables.Namespace(**config)


def save_config(config, config_file="config.json"):
    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)
    logger.info("Saved config")

#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import logging

import yaml
import reusables

logger = logging.getLogger("PyFoto.config")

default_config = dict(
    storage_directory="storage",
    # TODO add {date}, {time}, {type}, {hash}, {size}
    dir_names="{increment}",
    image_names="{increment}.{ext}",
    video_names="{increment}.{ext}",
    remove_source=False,
    folder_limit=1000,
    ignore_duplicates=False,
    video_dir_inc=0,
    image_dir_inc=0,
    video_file_inc=0,
    image_file_inc=0,
    video_sub_dir="videos",
    image_sub_dir="images",
    connect_string="sqlite:///pyfoto.sqlite"
)


def get_config(config_file="config.yaml"):
    """

    :param config_file:
    :return:
    """

    config = default_config.copy()

    if os.path.exists(config_file):
        with open(config_file) as f:
            config.update(yaml.load(f))
    logger.info("Loaded config")
    logger.debug("Config - {0}".format(config))

    config['video_dir'] = (config['storage_directory'] if not config.get('video_sub_dir') else
                           os.path.join(config['storage_directory'], config['video_sub_dir']))

    config['image_dir'] = (config['storage_directory'] if not config.get('image_sub_dir') else
                           os.path.join(config['storage_directory'], config['image_sub_dir']))

    return reusables.Namespace(**config)


def save_config(config, config_file="config.yaml"):
    """

    :param config:
    :param config_file:
    :return:
    """

    out_config = config.copy()
    del out_config['video_dir']
    del out_config['image_dir']
    with open(config_file, "w") as f:
        yaml.dump(out_config, f, default_flow_style=False)
    logger.info("Saved config")

#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import logging

import yaml
import reusables


default_config = dict(
    storage_directory="storage",
    # TODO add {date}, {time}, {type}, {hash}, {size}
    dir_names="{increment}",
    file_names="{increment}.{ext}",
    remove_source=False,
    folder_limit=1000,
    ignore_duplicates=False,
    dir_inc=0,
    file_inc=0,
    connect_string="sqlite:///pyfoto.sqlite"
)


def get_config(config_file: str="config.yaml") -> reusables.Namespace:
    """

    :param config_file:
    :return:
    """

    config = default_config.copy()

    if os.path.exists(config_file):
        with open(config_file) as f:
            config.update(yaml.load(f))
    else:
        logger.warning('Config file "{0}" does not exist, using '
                       'defaults which will be saved to it'.format(config_file))
    logger.debug("Loaded Config - {0}".format(config))

    return reusables.Namespace(**config)


def save_config(config: dict, config_file: str="config.yaml") -> None:
    """

    :param config:
    :param config_file:
    :return:
    """

    out_config = config.copy()
    dir_path = os.path.dirname(config_file)

    if dir_path and not os.path.exists(dir_path):
        logger.warning("Attempting to create new path to config file: "
                       "{0}".format(dir_path))
        os.makedirs(dir_path, exist_ok=True)

    with open(config_file, "w") as f:
        yaml.dump(out_config, f, default_flow_style=False)
    logger.debug("Saved config - {0}".format(out_config))


def get_stream_logger(module, level: int=0):
    new_logger = logging.getLogger("PyFoto.{}".format(module))
    sh = logging.StreamHandler()
    if level > 0:
        sh.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - '
                                  '%(levelname)s - %(message)s')
    sh.setFormatter(formatter)
    new_logger.addHandler(sh)
    if level > 0:
        new_logger.setLevel(level)

    return new_logger

logger = get_stream_logger("config", level=0)


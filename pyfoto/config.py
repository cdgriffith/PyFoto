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
    logger.info("Loaded config")
    logger.debug("Config - {0}".format(config))

    return reusables.Namespace(**config)


def save_config(config: dict, config_file: str="config.yaml") -> None:
    """

    :param config:
    :param config_file:
    :return:
    """

    out_config = config.copy()

    with open(config_file, "w") as f:
        yaml.dump(out_config, f, default_flow_style=False)
    logger.info("Saved config")

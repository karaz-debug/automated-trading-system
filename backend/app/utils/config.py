# utils/config.py

import yaml
import os
from typing import Dict, Any
from utils.logger import get_logger

logger = get_logger('ConfigLoader')

def load_config(config_file: str = 'config/config.yaml') -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    :param config_file: Path to the YAML configuration file relative to the utils directory.
    :return: Dictionary containing configuration
    """
    try:
        # Get the absolute path of the current file (config.py)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the absolute path to the config file
        config_path = os.path.join(current_dir, '..', config_file)
        config_path = os.path.normpath(config_path)  # Normalize the path

        logger.debug(f"Attempting to load config from: {config_path}")

        if not os.path.exists(config_path):
            logger.error(f"Configuration file not found at path: {config_path}")
            raise FileNotFoundError(f"Configuration file not found at path: {config_path}")

        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)

        logger.info(f"Configuration loaded successfully from: {config_path}")
        return config

    except FileNotFoundError as fnf_error:
        logger.error(f"FileNotFoundError: {fnf_error}")
        raise
    except yaml.YAMLError as yaml_error:
        logger.error(f"YAMLError: Failed to parse YAML file. {yaml_error}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        raise

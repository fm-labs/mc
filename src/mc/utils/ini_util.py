import configparser
import os


def read_ini_file(file_path: str) -> configparser.ConfigParser:
    """
    Read an INI file and return a ConfigParser object.

    :param file_path: Path to the INI file.
    :return: ConfigParser object with the INI file contents.
    """
    config = configparser.ConfigParser()
    if not os.path.exists(file_path):
        return config  # Return empty config if file does not exist

    with open(file_path, "r") as config_file:
        config.read_file(config_file)
    return config


def write_ini_file(file_path: str, config: configparser.ConfigParser) -> None:
    """
    Write a ConfigParser object to an INI file.

    :param file_path: Path to the INI file.
    :param config: ConfigParser object to write.
    """
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w") as config_file:
        config.write(config_file)


def update_ini_section(file_path: str, section: str, kv: dict) -> None:
    """
    Add a section to an INI file.

    :param file_path: Path to the INI file.
    :param section: Section name to add.
    :param kv: Key-value pairs to add under the section.
    """
    config = read_ini_file(file_path)
    if "section" in config:
        print(f"Section '{section}' already exists in {file_path}. Overwriting.")
    config[section] = kv
    write_ini_file(file_path, config)

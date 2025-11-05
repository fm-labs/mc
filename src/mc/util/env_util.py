import os


def load_envfile(env_file: str, penv: dict) -> dict:
    """
    Load environment file into a dictionary

    :param env_file: Path to the environment file
    :param penv: Dictionary to load the environment file into
    :return:
    """
    if penv is None:
        penv = dict()

    if not os.path.exists(env_file):
        raise FileNotFoundError(f"Environment file {env_file} does not exist")

    with open(env_file, 'r') as f:
        for line in f.readlines():
            if line.strip() and not line.startswith('#'):
                k, v = line.split('=', 1)
                penv[k] = v.strip()
    return penv

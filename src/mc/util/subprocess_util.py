import subprocess

def kwargs_to_cmdargs(kwargs) -> list:
    """
    Map kwargs to command line arguments.

    :param kwargs:
    :return:
    """
    args = []
    for k, v in kwargs.items():
        if v is not None and v is not False:
            if len(k) == 1 and type(v) is bool:
                args.append(f"-{k}")
                continue

            args.append(f"--{k.replace('_', '-')}")
            if type(v) is not bool:
                args.append(str(v))
    return args


def run_command(cmd: str | list):
    """
    Invoke Docker Command in Local Shell (Blocking)
    """
    try:
        return subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        return e.output



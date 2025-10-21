import os

def list_files_in_dir_recursive(directory: str, strip_base: bool = True) -> list:
    """
    Lists all files in a directory recursively.
    """

    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if strip_base:
                file_list.append(os.path.relpath(os.path.join(root, file), directory))
            else:
                file_list.append(os.path.join(root, file))
    return file_list
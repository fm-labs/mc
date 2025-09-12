import os


def write_file(file_path: str, content: str, overwrite: bool = False) -> bool:
    """
    Write content to a file.

    :param file_path: Path to the file to write.
    :param content: Content to write to the file.
    :param overwrite: If True, overwrite the file if it exists.
    :return: True if the file was written successfully, False otherwise.
    """
    try:
        if not overwrite and os.path.exists(file_path):
            print(f"File {file_path} already exists. Use overwrite=True to overwrite.")
            return False

        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing file {file_path}: {e}")
        return False


def read_file(file_path: str) -> str:
    """
    Read content from a file.

    :param file_path: Path to the file to read.
    :return: Content of the file as a string.
    """
    try:
        with open(file_path, "r") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""
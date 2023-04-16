"""File operations for AutoGPT"""
import os
import os.path
from pathlib import Path
from typing import Generator, List
from autogpt.config import Config
CFG = Config()
# Set a dedicated folder for file I/O
WORKING_DIRECTORY = Path(os.getcwd()) / "auto_gpt_workspace"

# Create the directory if it doesn't exist
if not os.path.exists(WORKING_DIRECTORY):
    os.makedirs(WORKING_DIRECTORY)

LOG_FILE = "file_logger.txt"
LOG_FILE_PATH = WORKING_DIRECTORY / LOG_FILE
WORKING_DIRECTORY = str(WORKING_DIRECTORY)


def check_duplicate_operation(operation: str, filename: str) -> bool:
    """Check if the operation has already been performed on the given file

    Args:
        operation (str): The operation to check for
        filename (str): The name of the file to check for

    Returns:
        bool: True if the operation has already been performed on the file
    """
    log_content = read_file(LOG_FILE)
    log_entry = f"{operation}: {filename}\n"
    return log_entry in log_content


def log_operation(operation: str, filename: str) -> None:
    """Log the file operation to the file_logger.txt

    Args:
        operation (str): The operation to log
        filename (str): The name of the file the operation was performed on
    """
    log_entry = f"{operation}: {filename}\n"

    # Create the log file if it doesn't exist
    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
            f.write("File Operation Logger ")

    append_to_file(LOG_FILE, log_entry)


def safe_join(base: str, *paths) -> str:
    """Join one or more path components intelligently.

    Args:
        base (str): The base path
        *paths (str): The paths to join to the base path

    Returns:
        str: The joined path
    """
    if str(CFG.working_directory_restricted).lower() == "true":
        new_path = os.path.normpath(os.path.join(base, *paths))
        if os.path.commonprefix([base, new_path]) != base:
            raise ValueError("Attempted to access outside of working directory.")
    else:
        new_path = os.path.normpath(os.path.join("/", *paths))
    return new_path


def split_file(
    content: str, max_length: int = 4000, overlap: int = 0
) -> Generator[str, None, None]:
    """
    Split text into chunks of a specified maximum length with a specified overlap
    between chunks.

    :param content: The input text to be split into chunks
    :param max_length: The maximum length of each chunk,
        default is 4000 (about 1k token)
    :param overlap: The number of overlapping characters between chunks,
        default is no overlap
    :return: A generator yielding chunks of text
    """
    start = 0
    content_length = len(content)

    while start < content_length:
        end = start + max_length
        if end + overlap < content_length:
            chunk = content[start : end + overlap]
        else:
            chunk = content[start:content_length]
        yield chunk
        start += max_length - overlap


def read_file(filename: str) -> str:
    """Read a file and return the contents

    Args:
        filename (str): The name of the file to read

    Returns:
        str: The contents of the file
    """
    try:
        filepath = safe_join(WORKING_DIRECTORY, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error: {str(e)}"


def ingest_file(
    filename: str, memory, max_length: int = 4000, overlap: int = 200
) -> None:
    """
    Ingest a file by reading its content, splitting it into chunks with a specified
    maximum length and overlap, and adding the chunks to the memory storage.

    :param filename: The name of the file to ingest
    :param memory: An object with an add() method to store the chunks in memory
    :param max_length: The maximum length of each chunk, default is 4000
    :param overlap: The number of overlapping characters between chunks, default is 200
    """
    try:
        print(f"Working with file {filename}")
        content = read_file(filename)
        content_length = len(content)
        print(f"File length: {content_length} characters")

        chunks = list(split_file(content, max_length=max_length, overlap=overlap))

        num_chunks = len(chunks)
        for i, chunk in enumerate(chunks):
            print(f"Ingesting chunk {i + 1} / {num_chunks} into memory")
            memory_to_add = (
                f"Filename: {filename}\n" f"Content part#{i + 1}/{num_chunks}: {chunk}"
            )

            memory.add(memory_to_add)

        print(f"Done ingesting {num_chunks} chunks from {filename}.")
    except Exception as e:
        print(f"Error while ingesting file '{filename}': {str(e)}")


def write_to_file(filename: str, text: str) -> str:
    """Write text to a file

    Args:
        filename (str): The name of the file to write to
        text (str): The text to write to the file

    Returns:
        str: A message indicating success or failure
    """
    if check_duplicate_operation("write", filename):
        return "Error: File has already been updated."
    try:
        filepath = safe_join(WORKING_DIRECTORY, filename)
        directory = os.path.dirname(filepath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        log_operation("write", filename)
        return "File written to successfully."
    except Exception as e:
        return f"Error: {str(e)}"


def append_to_file(filename: str, text: str) -> str:
    """Append text to a file

    Args:
        filename (str): The name of the file to append to
        text (str): The text to append to the file

    Returns:
        str: A message indicating success or failure
    """
    try:
        filepath = safe_join(WORKING_DIRECTORY, filename)
        with open(filepath, "a") as f:
            f.write(text)
        log_operation("append", filename)
        return "Text appended successfully."
    except Exception as e:
        return f"Error: {str(e)}"


def delete_file(filename: str) -> str:
    """Delete a file

    Args:
        filename (str): The name of the file to delete

    Returns:
        str: A message indicating success or failure
    """
    if check_duplicate_operation("delete", filename):
        return "Error: File has already been deleted."
    try:
        filepath = safe_join(WORKING_DIRECTORY, filename)
        os.remove(filepath)
        log_operation("delete", filename)
        return "File deleted successfully."
    except Exception as e:
        return f"Error: {str(e)}"


def search_files(directory: str) -> List[str]:
    """Search for files in a directory

    Args:
        directory (str): The directory to search in

    Returns:
        List[str]: A list of files found in the directory
    """
    found_files = []

    if directory in {"", "/"}:
        search_directory = WORKING_DIRECTORY
    else:
        search_directory = safe_join(WORKING_DIRECTORY, directory)

    for root, _, files in os.walk(search_directory):
        for file in files:
            if file.startswith("."):
                continue
            relative_path = os.path.relpath(os.path.join(root, file), WORKING_DIRECTORY)
            found_files.append(relative_path)

    return found_files

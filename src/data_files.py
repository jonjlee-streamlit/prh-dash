import os
import streamlit as st

# Location of data files: <app root>/data/
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def get():
    """
    Return list of data files.
    In the future, can specify by environment or streamlit configuration var"""
    return get_on_disk()


def get_on_disk():
    """Return list of files on local disk, specified by global BASE_PATH"""
    if not os.path.isdir(BASE_PATH):
        return []

    return [os.path.join(BASE_PATH, local) for local in os.listdir(BASE_PATH)]


def update_on_disk(files: list, remove_existing_first: bool):
    """
    Accepts a list of file objects that should have a read() method (eg. st.UploadedFile returned by st.file_uploader)
    and writes these files to the local data directory.
    If remove_existing_first is True, deletes contents of data directory before writing new files.
    """
    if files is None or len(files) == 0:
        return

    # Ensure base data directory exists
    os.makedirs(BASE_PATH, exist_ok=True)

    # Delete all files if requested
    if remove_existing_first:
        for local in os.listdir(BASE_PATH):
            os.remove(os.path.join(BASE_PATH, local))

    # Save new files to data dir
    for file in files:
        with open(os.path.join(BASE_PATH, file.name), "wb") as local:
            local.write(file.read())

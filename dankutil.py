import os


# Create a file if it doesn't exist
def ensure_file_exists(fname):
    if not os.path.isfile(fname):
        open(fname, "a").close()

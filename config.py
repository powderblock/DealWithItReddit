import re
import os
import dankutil


def get_config(fname, setup_items=[], default_items={}):
    dankutil.ensure_file_exists(fname)
    with open(fname, "r") as f:
        text = f.read()

    # Ensure that the file ends with a newline
    if len(text) != 0 and text[-1:] != "\n":
        with open(fname, "a") as f:
            f.write("\n")

    # Extract all of the lines from the file
    # They look like:
    # key = "value"
    # key2 = 'value2'

    line_regex = re.compile(r"(.+?) ?= ?(\"(.+)\"|\'(.+)\')")
    config = {i.group(1): i.group(3) for i in line_regex.finditer(text)}

    # For each key that doesn't exist in the file, get the user's input
    # and use that to add it to the file and the config

    with open(fname, "a") as f:
        for name in setup_items:
            if name not in config:
                # Get the new value for the currently needed key
                new_value = raw_input("{} = ".format(name))
                config[name] = new_value

                # Write the newly chosen value to the config file
                f.write('{} = "{}"\n'.format(name, new_value))

        for name in default_items:
            if name not in config:
                # Perform the same type of update using the default items
                new_value = default_items[name]
                config[name] = new_value
                f.write('{} = "{}"\n'.format(name, new_value))

    return config

import dankutil
from datetime import datetime


def karma_yesterday():
    # Get all the karma data from the file into a list
    dankutil.ensure_file_exists("karma.txt")
    with open("karma.txt", "r") as karmafile:
        karma = karmafile.readlines()

    # Remove all the surrounding whitespace
    karma = [line.strip() for line in karma]
    # Split all of the strings into tuples on the comma, and remove invalid entries
    karma = [tuple(line.split(",")) for line in karma if len(line.split(",")) == 2]
    # Convert the karma string to an int and the timestamp to a date
    try:
        datefmt = "%Y-%m-%d %H:%M:%S.%f"

    except:
        datefmt = "%Y-%m-%d %H:%M:%S.000000"
    karma = [(datetime.strptime(d.strip(), datefmt), int(k)) for k, d in karma]
    # Sort the karma based on datetime
    karma.sort()
    # Remove the time information from the datetime, we don't care about it anymore
    karma = [(dt.date(), k) for dt, k in karma]

    # The `days` will contain the first entry from each day
    # We insert the first entry as the base case, since it will always be
    # the first we have from that day (we sorted it)
    days = [karma[0]]
    for day in karma:
        # If this entry is from a new day add it to `days`
        if day[0] != days[-1][0]:
            days.append(day)

    # Get rid of the information about what day it is,
    # we only care about start-of-day karma
    days = [day[1] for day in days]
    # Return the amount of karma gained during the previous day
    return days[-1] - days[-2]

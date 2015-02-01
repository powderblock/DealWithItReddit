import time
import re
import os
from datetime import datetime

def karma_yesterday():
    # Create karma.txt if it doesn't exist
    if not os.path.isfile("karma.txt"):
        open("karma.txt", "a").close()

    # Get all the karma data from the file into a list
    with open("karma.txt", "r") as karmafile:
        karma = karmafile.readlines()

    # Remove all the surrounding whitespace
    karma = [line.strip() for line in karma]
    # Split all of the strings into tuples on the comma, and remove invalid entries
    karma = [tuple(line.split(",")) for line in karma if len(line.split(",")) == 2]
    # Convert the karma string to an int and the timestamp to a date
    datefmt = "%Y-%m-%d %H:%M:%S.%f"
    karma = [(datetime.strptime(d.strip(), datefmt), int(k)) for k, d in karma]
    print karma[245][1]
    # Sort the karma based on datetime
    karma.sort()
    # Remove the time information from the datetime, we don't care about it anymore
    karma = [(dt.date(), k) for dt, k in karma]

    # The `days` will contain the first entry from each day
    # We insert the first entry as the base case, since it will always be
    # the first we have from that day (we sorted it)
    days = [karma[0]]
    global averageKarma
    for day in karma:
        # If this entry is from a new day add it to `days`
        if day[0] != days[-1][0]:
            days.append(day)

        

    # Get rid of the information about what day it is,
    # we only care about start-of-day karma
    days = [day[1] for day in days]
    # Return the amount of karma gained during the previous day
    rawKarma = [line.split(',')[0] for line in open('karma.txt')]

    #for i in range(len(rawKarma)):
        #print rawKarma[-i]

    global soFarKarma
    soFarKarma = int(rawKarma[-1]) - days[-1]
    print soFarKarma

karma_yesterday()

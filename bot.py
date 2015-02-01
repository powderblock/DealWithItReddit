import praw
import urllib
import cv2
import numpy as np
from PIL import Image
import time
import re
import pyimgur
import os
import tweepy
from datetime import datetime

# Eye Classifier
eyeData = "xml/eyes.xml"
faceData = "xml/faces.xml"
eyeClass = cv2.CascadeClassifier(eyeData)
faceClass = cv2.CascadeClassifier(faceData)

# Glasses Asset
glasses = cv2.imread('assets/glasses.png', cv2.IMREAD_UNCHANGED)
dealWithItText = cv2.imread('assets/dealWithItText.png', cv2.IMREAD_UNCHANGED)
ratio = glasses.shape[1] / glasses.shape[0]
ratioText = dealWithItText.shape[1] / dealWithItText.shape[0]

# How much we are going to downscale image while processing it.
DOWNSCALE = 4
foundImage = False
eyesInImage = False

ONE_HOUR = 60*60
last_profile_update = 0

# List of posts already processed.
already_done = set()

line_regex = re.compile(r"(?<=:).+")
post_regex = re.compile(r"().+")
reddit = line_regex.finditer(open("redditInfo.txt", "a+").read())
posts = post_regex.finditer(open("posts.txt", "a+").read())
imgur = line_regex.finditer(open("imgurInfo.txt", "a+").read())
twitter = line_regex.finditer(open("twitterInfo.txt", "a+").read())

redditItems = [item.group(0).strip() for item in reddit]
imgurItems = [item.group(0).strip() for item in imgur]
twitterItems = [item.group(0).strip() for item in twitter]
postItems = [item.group(0).strip() for item in posts]

# Super secret user information:
client_id = imgurItems[0]
username = redditItems[0]
password = redditItems[1]

# Auth Twitter:
consumer_key = twitterItems[0]
consumer_secret = twitterItems[1]

access_token = twitterItems[2]
access_token_secret = twitterItems[3]

# Auth api client
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.secure = True
auth.set_access_token(access_token, access_token_secret)

# Create blacklist_subs.txt if it doesn't exist
if not os.path.isfile("blacklist_subs.txt"):
    open("blacklist_subs.txt", "a").close()

# Get all the blacklisted subs, put them into a list
with open("blacklist_subs.txt", "r") as blacklist_subs:
    blacklisted_subs = blacklist_subs.readlines()
    blacklisted_subs = [sub.strip('\n') for sub in blacklisted_subs]

# Create blacklist_subs.txt if it doesn't exist
if not os.path.isfile("blacklist_users.txt"):
    open("blacklist_users.txt", "a").close()
    
# Get all the blacklisted subs, put them into a list
with open("blacklist_users.txt", "r") as blacklist_users:
    blacklisted_users = blacklist_users.readlines()
    blacklisted_users = [user.strip('\n') for user in blacklisted_users]

api = tweepy.API(auth)

# client name
r = praw.Reddit('/u/powderblock Glasses Bot')

# Message template for formatting posts
message_template = """[DEAL WITH IT]({image_link})

***

^[feedback](http://www.reddit.com/message/compose/?to=powderblock&subject=DealWithItbot%20Feedback) \
^[source](https://github.com/powderblock/PyDankReddit) \
^[creator](http://www.reddit.com/user/powderblock/)"""

botAccount = r.get_redditor('DealWithItbot')

# File to load post IDs from
postsFile = open("posts.txt", "a+")

for post in range(0, len(postItems)):
    already_done.add(str(postItems[post]))


def collide(eye, face):
    leftA = eye[0]
    rightA = leftA + eye[2]
    topA = eye[2] - eye[3]
    bottomA = eye[3]
    leftB = face[0]
    rightB = leftB + face[2]
    topB = face[2] - face[3]
    bottomB = face[3]
    # If a collision is found
    if rightA > leftB and leftA < rightB and bottomA > topB and topA < bottomB:
        return True
    else:
        return False


def process_image(name, frame, eyes):
    for eye in eyes:
        x, y, w, h = [v * DOWNSCALE for v in eye]
        h = w / ratio
        y += h / 2
        # resize glasses to a new var called small glasses
        smallglasses = cv2.resize(glasses, (w, h))
        # the area you want to change
        bg = frame[y:y+h, x:x+w]
        bg *= np.atleast_3d(255 - smallglasses[:, :, 3])/255.0
        bg += smallglasses[:, :, 0:3] * np.atleast_3d(smallglasses[:, :, 3])
        # put the changed image back into the scene
        frame[y:y+h, x:x+w] = bg
        print("Found image. Writing image.")
        savedImage = name.replace(":", "").replace("/", "")
        cv2.imwrite(str(savedImage), frame)
        print(("Saved: ") + str(savedImage))
        im = pyimgur.Imgur(client_id)
        global uploaded_image
        uploaded_image = im.upload_image(savedImage, title=savedImage)
        os.remove(str(savedImage))
        print("Uploaded image with glasses: {}".format(uploaded_image.link))


# Check if a given url fits our needs
def is_image(url):
    return (url[-4:] == ".png" or url[-4:] == ".jpg" or url[-5:] == ".jpeg")


def removeNeg():
    for i in user.get_comments():
        if i.score <= int(-1):
            i.delete()
            print("Removed comment because score was too low.")


# function to check for duplicate comments:
def removeDupes():
    comments = set()
    for i in user.get_comments():
        if i.submission.id in comments:
            # Check and make sure the bot made comment
            # Creator may comment on a single post multiple times within several minutes.
            if "DEAL WITH IT" in i.body:
                print("Duplicate post found. Removing post.")
                i.delete()
            
        comments.add(i.submission.id)


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
    try:
        datefmt = "%Y-%m-%d %H:%M:%S.%f"

    except:
        datefmt = "%Y-%m-%d %H:%M:%S"
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


def checkMessages():
    for msg in r.get_unread(limit=None):
        available = 109 - len(unicode(msg.author))
        body = msg.body if len(unicode(msg.body)) <= available else unicode((msg.body)[:available]+ "\u2026")
        # Mark as read goes before updating so if the message breaks, don't get stuck in a loop:
        msg.mark_as_read()
        #Tweet about the new message
        try:
            api.update_status("'{body}' -/u/{author} {link}{context}".format(
            body=body,
            author=msg.author,
            link=msg.permalink,
            context="?context=3"
            ))
        except:
            print("Tweet was not made. Skipping.")


# main loop
while True:
    eyesInImage = False
    foundImage = False
    # Auth Reddit
    r.login(username, password)
    user = r.get_redditor('DealWithItbot')
    # Auth Twitter
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.secure = True
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)
    count = 0
    for post in r.get_subreddit('all').get_new(limit=20):
        done = post in already_done
        subreddit = post.subreddit
        author = post.author
        if not done and subreddit not in blacklisted_subs and author not in blacklisted_users:
            count += 1
            already_done.add(post)
            postsFile.write(post.id + "\n")
            postsFile.flush()
            if is_image(post.url):
                filename = str(post.url).replace(":", "").replace("/", "")
                foundImage = True
                response = urllib.urlopen(post.url)

                # load the image we want to detect features on
                # Convert rawImage to Mat
                filear = np.asarray(bytearray(response.read()), dtype=np.uint8)
                frame = cv2.imdecode(filear, cv2.CV_LOAD_IMAGE_UNCHANGED)

                # Make sure image is valid.
                if frame is None or frame.size is None:
                    print("Error, couldn't load image, skipping.")
                    # Skip to next image
                    continue

                # If the image is too large, skip it:
                if frame.shape[0] > 5000 or frame.shape[1] > 5000:
                    print("Image is too large, skipping.")
                    continue

                # Protector against animated files:
                if frame.shape[0] == 0 or frame.shape[1] == 0:
                    print("Image has a width or height of 0, skipping. (Image maybe be animated?)")
                    continue

                minisize = (frame.shape[1]/DOWNSCALE, frame.shape[0]/DOWNSCALE)
                miniframe = cv2.resize(frame, minisize)
                eyes = eyeClass.detectMultiScale(miniframe)
                faces = faceClass.detectMultiScale(miniframe)
                eyes_to_use = []
                for eye in eyes:
                    for face in faces:
                        if collide(eye, face):
                            eyes_to_use.append(eye)
                            eyesinImage = True
                            # Go on to the next eye
                            break

                if len(eyes_to_use) > 0:
                    print("Found eyes in the image: " + str(post.url))
                    print("Processing image.")
                    process_image(str(post.url), frame, eyes_to_use)
                    submission = r.get_submission(submission_id=post.id)
                    # Make a link with text deal with it, link points to the uploaded image.
                    message = message_template.format(image_link = uploaded_image.link)
                    try:
                        # Leave the comment
                        comment = submission.add_comment(message)
                        print("Comment has been left. Here's what it says: " +
                              message)
                        try:
                            if submission.over_18:
                                NSFW = "[Not Safe For Work!]"
                            if not submission.over_18:
                                NSFW = "[Safe For Work!]"
                            # Post to twitter
                            api.update_status(("New Post! {link} {hashtag} " + NSFW).format(
                                link=str(comment.permalink),
                                hashtag = "#reddit"
                            ))
                            print("Tweet made!")
                        except:
                            print("Tweet was not made. Skipping.")

                    # If you are commenting too much, sleep!
                    except praw.errors.RateLimitExceeded:
                        print("**Comment time limit exceeded. Sleeping.**")
                        time.sleep(600)

    if not foundImage and not eyesInImage:
        print("No valid image{} were found.".format(
            "s" if count > 1 else ""
        ))
    if foundImage and not eyesInImage:
        print("No eyes detected in image{}".format(
            "s" if count > 1 else ""
        ))

    checkMessages()
    removeDupes()
    removeNeg()

    time.sleep(30)

    # Only update the status once per hour
    if (time.time() - last_profile_update > ONE_HOUR):
        last_profile_update = time.time()
        # Do this check BEFORE writing to karma.txt
        # Otherwise we are going to be reading current karma
        with open("karma.txt", "r") as karmafile:
            lines = [line.split(',')[0] for line in karmafile]

        lastKarma = lines[-1]
        karma_status = "Currently I have {karma} karma, yesterday I gained {yesterday} karma.".format(
            karma=botAccount.comment_karma,
            yesterday=karma_yesterday()
        )
        api.update_profile(description=karma_status)
        print(karma_status)
        # Open karma.txt for karma saving:
        with open("karma.txt", "a+") as karmaFile:
            karmaFile.write("{karma}, {timeAndDate}\n".format(
                karma = botAccount.comment_karma,
                timeAndDate = str(datetime.now())
            ))

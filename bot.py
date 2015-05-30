import praw
import urllib
import cv2
import numpy as np
from PIL import Image
import time
import pyimgur
import os
import tweepy
from datetime import datetime
import config
import dankutil
import karma

# Force the user to provide values for these on the command line if they're not present
# in the config file
required_properties = [
    'reddit_username', 'reddit_password', 'imgur_client_id', 'twitter_consumer_key',
    'twitter_consumer_secret', 'twitter_access_token', 'twitter_access_token_secret',
]
# Define default values for properties if they're not present in the config file
default_properties = {
    'eye_data': 'xml/eyes.xml', 'face_data': 'xml/faces.xml',
    'glasses_image': 'assets/glasses.png'
}
conf = config.get_config("config.txt", required_properties, default_properties)

# Eye Classifier
eyeClass = cv2.CascadeClassifier(conf['eye_data'])
faceClass = cv2.CascadeClassifier(conf['face_data'])

# Glasses Asset
glasses = cv2.imread(conf['glasses_image'], cv2.IMREAD_UNCHANGED)
ratio = glasses.shape[1] / glasses.shape[0]

# How much we are going to downscale image while processing it.
DOWNSCALE = 4
foundImage = False
eyesInImage = False

ONE_HOUR = 60*60
last_profile_update = 0

# Auth twitter API client
auth = tweepy.OAuthHandler(conf['twitter_consumer_key'], conf['twitter_consumer_secret'])
auth.secure = True
auth.set_access_token(conf['twitter_access_token'], conf['twitter_access_token_secret'])

# Get all the blacklisted subs, put them into a set
dankutil.ensure_file_exists("blacklist_subs.txt")
with open("blacklist_subs.txt", "r") as blacklist_subs:
    blacklisted_subs = {sub.strip() for sub in blacklist_subs.readlines()}

# Get all the blacklisted subs, put them into a set
dankutil.ensure_file_exists("blacklist_users.txt")
with open("blacklist_users.txt", "r") as blacklist_users:
    blacklisted_users = {user.strip() for user in blacklist_users.readlines()}

api = tweepy.API(auth)

# Reddit client name
r = praw.Reddit('/u/powderblock Glasses')
botAccount = r.get_redditor(conf['reddit_username'])

# Message template for formatting posts
message_template = """[DEAL WITH IT]({{image_link}})

***

^[feedback](http://www.reddit.com/message/compose/\
?to=powderblock&subject={botname}%20Feedback) \
^[source](https://github.com/powderblock/PyDankReddit) \
^[creator](http://www.reddit.com/user/powderblock/)""".format(
    botname=conf['reddit_username']
)

# File to load post IDs from
dankutil.ensure_file_exists("posts.txt")
with open("posts.txt", "r") as postsFile
    # A set of posts already processed based on the file
    already_done = {item.strip() for item in postsFile.read().split("\n")}

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


def removeNeg(user):
    for i in user.get_comments():
        if i.score <= int(-1):
            i.delete()
            print("Removed comment because score was too low.")


# function to check for duplicate comments:
def removeDupes(user):
    comments = set()
    for i in user.get_comments():
        if i.submission.id in comments:
            # Check and make sure the bot made comment
            # Creator may comment on a single post multiple times within several minutes.
            if "DEAL WITH IT" in i.body:
                print("Duplicate post found. Removing post.")
                i.delete()

        comments.add(i.submission.id)


def checkMessages():
    for msg in r.get_unread(limit=None):
        msg.mark_as_read()
        try:
            message_text = '{body} -/u/{author} {link}{context}'.format(
                body=body,
                author=msg.author,
                link=msg.permalink,
                context="?context=3"
            )
            r.send_message('powderblock', 'New message!', message_text)
        except:
            print("Message was not sent.")

        available = 109 - len(unicode(msg.author))
        if len(unicode(msg.body)) <= available:
            body = msg.body
        else:
            body = unicode((msg.body)[:available] + "\u2026")

        # Mark as read goes before updating so if the message breaks, don't get stuck in a loop:
        # Tweet about the new message
        try:
            api.update_status(status="'{body}' -/u/{author} {link}{context}".format(
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
    r.login(conf['reddit_username'], conf['reddit_password'])
    user = r.get_redditor(conf['reddit_username'])
    # Auth Twitter
    auth = tweepy.OAuthHandler(conf['twitter_consumer_key'], conf['twitter_consumer_secret'])
    auth.secure = True
    auth.set_access_token(conf['twitter_access_token'], conf['twitter_access_token_secret'])

    api = tweepy.API(auth)
    count = 0
    for post in r.get_subreddit('all').get_new(limit=20):
        done = post in already_done
        blacklisted = (post.subreddit in blacklisted_subs
                       or post.author in blacklisted_users)
        if not done and not blacklisted:
            count += 1
            already_done.add(post)
            # Warning: This is a potential performance bottleneck, if that is ever a problem
            with open("posts.txt", "a") as postsFile:
                postsFile.write(post.id + "\n")

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
                    message = message_template.format(image_link=uploaded_image.link)
                    try:
                        # Leave the comment
                        comment = submission.add_comment(message)
                        print("Comment has been left. Here's what it says: " +
                              message)
                        try:
                            if submission.over_18:
                                NSFW = "[Not Safe For Work!]"
                            else:
                                NSFW = "[Safe For Work!]"
                            # Post to twitter
                            api.update_status(status="New Post! {link} {hashtag} {nsfwtag}".format(
                                link=str(comment.permalink),
                                hashtag="#reddit",
                                nsfwtag=NSFW
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
    removeDupes(user)
    removeNeg(user)

    time.sleep(30)

    # Only update the status once per hour
    if (time.time() - last_profile_update > ONE_HOUR):
        last_profile_update = time.time()
        # Do this check BEFORE writing to karma.txt
        # Otherwise we are going to be reading current karma
        with open("karma.txt", "r") as karmafile:
            lines = [line.split(',')[0] for line in karmafile]

        lastKarma = lines[-1]
        karma_status = "Currently I have {karma} karma, yesterday I gained {gain} karma.".format(
            karma=botAccount.comment_karma,
            gain=karma.karma_yesterday()
        )
        api.update_profile(description=karma_status)
        print(karma_status)
        # Open karma.txt for karma saving:
        with open("karma.txt", "a+") as karmaFile:
            karmaFile.write("{karma}, {timeAndDate}\n".format(
                karma=botAccount.comment_karma,
                timeAndDate=str(datetime.now())
            ))

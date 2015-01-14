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

# List of posts already processed.
already_done = []

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

#Auth Twitter:
consumer_key = twitterItems[0]
consumer_secret = twitterItems[1]

access_token = twitterItems[2]
access_token_secret = twitterItems[3]

# Auth api client
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.secure = True
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

# client name
r = praw.Reddit('/u/powderblock Glasses Bot')

botAccount = r.get_redditor('DealWithItbot')

lines = [line.split(',')[0] for line in open('karma.txt')]

lastKarma = lines[len(lines) - 1]

#Do this check BEFORE writing to karma.txt
#Otherwise we are going to be reading current karma
if(botAccount.comment_karma > int(lastKarma)):
    print "Bot account is higher than last recorded karma"
    print botAccount.comment_karma
    api.update_profile(description="Karma: {}".format(botAccount.comment_karma))
    #Open karma.txt for karma saving:
    with open("karma.txt", "a+") as karmaFile:
        karmaFile.write("{karma}, {timeAndDate}\n".format(karma = botAccount.comment_karma, timeAndDate = str(datetime.now())))
	#Close the file:
        karmaFile.close()

# File to load post IDs from
postsFile = open("posts.txt", "a+")

for post in range(0, len(postItems)):
    already_done.append(str(postItems[post]))


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
        if post not in already_done:
            count += 1
            already_done.append(post)
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

                #If the image is too large, skip it:
                if frame.shape[0] > 5000 or frame.shape[1] > 5000:
                    print("Image is too large, skipping.")
                    continue

                #Protector against animated files:
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
                    message = '[DEAL WITH IT]({image_link})\n\n***\n\n^[feedback](http://www.reddit.com/message/compose/?to=powderblock&subject=DealWithItbot%20Feedback) ^[source](https://github.com/powderblock/PyDankReddit) ^[creator](http://www.reddit.com/user/powderblock/)'.format(image_link = uploaded_image.link)
                    try:
                        # Leave the comment
                        comment = submission.add_comment(message)
                        print("Comment has been left. Here's what it says: " +
                              message)
                        try:
                            # Post to twitter
                            api.update_status(("New Post! {link} {hashtag}").format(link = str(comment.permalink), hashtag = "#reddit"))
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

    for msg in r.get_unread(limit=None):
        available = 109 - len(str(msg.author))
        body = msg.body if len(str(msg.body)) <= available else str(msg.body)[:available]+ "\u2026"
        #Mark as read goes before updating so if the message breaks, don't get stuck in a loop:
        msg.mark_as_read()
        #Tweet about the new message
        api.update_status("'{body}' -/u/{author} {link}{context}".format(body=body,author=msg.author,link=msg.permalink, context="?context=3"))


    for i in user.get_comments():
        if i.score <= int(-1):
            i.delete()

    time.sleep(30)

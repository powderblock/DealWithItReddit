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

# Eye Classifier
eyeData = "xml/eyes.xml"
faceData = "xml/faces.xml"
eyeClass = cv2.CascadeClassifier(eyeData)
faceClass = cv2.CascadeClassifier(faceData)
# Glasses Asset
glasses = cv2.imread('assets/glasses.png', cv2.IMREAD_UNCHANGED)
ratio = glasses.shape[1] / glasses.shape[0]
# How much we are going to downscale image while processing it.
DOWNSCALE = 4
foundImage = False
eyesInImage = False

# List of posts already processed.
already_done = []

line_regex = re.compile(r"(?<=:).+")
post_regex = re.compile(r"().+")
reddit = line_regex.finditer(open("redditInfo", "r").read())
posts = post_regex.finditer(open("posts", "r").read())
imgur = line_regex.finditer(open("imgurInfo", "r").read())
twitter = line_regex.finditer(open("twitterInfo", "r").read())

redditItems = [item.group(0).strip() for item in reddit]
imgurItems = [item.group(0).strip() for item in imgur]
twitterItems = [item.group(0).strip() for item in twitter]
postItems = [item.group(0).strip() for item in posts]

# File to load post IDs from
postsFile = open("posts", "a")

for post in range(0, len(postItems)):
    already_done.append(str(postItems[post]))

# Super secret user information:
client_id = imgurItems[0]
username = redditItems[0]
password = redditItems[1]

consumer_key = twitterItems[0]
consumer_secret = twitterItems[1]

access_token = twitterItems[2]
access_token_secret = twitterItems[3]


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
    # Otherwise
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
        print(uploaded_image.link)


# Check if a given url fits our needs
def is_imgur_url(url):
    return "imgur.com" in url and (".jpg" in url or ".png" in url)

# main loop
while True:
    eyesInImage = False
    foundImage = False
    # client name
    r = praw.Reddit('/u/powderblock Glasses Bot')
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
            if is_imgur_url(post.url):
                filename = str(post.url).replace(":", "").replace("/", "")
                foundImage = True
				try: response = urllib.urlopen(post.url)
				except URLError as e:
					print e.reason

                # load the image we want to detect features on
                # Convert rawImage to Mat
                filear = np.asarray(bytearray(response.read()), dtype=np.uint8)
                frame = cv2.imdecode(filear, cv2.CV_LOAD_IMAGE_UNCHANGED)

                # Make sure image is valid.
                if frame is None or frame.size is None:
                    print("Error, couldn't load image, skipping.")
                    # Skip to next image
                    continue

                if frame.shape[0] > 5000 or frame.shape[1] > 5000:
                    print("Image is too large, skipping.")
                    continue

                if frame.shape[0] == 0 or frame.shape[1] == 0:
                    print("Image has a width or height of 0, skipping.")
                    continue

                minisize = (frame.shape[1]/DOWNSCALE,
                            frame.shape[0]/DOWNSCALE)
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
                    message = '[DEAL WITH IT]('+uploaded_image.link+')'
                    try:
                        # Leave the comment
                        comment = submission.add_comment(message)
                        print("Comment has been left. Here's what it says: " +
                              message)
                        try:
                            # Post to twitter
                            api.update_status(("New Post! ") + comment.permalink)
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
        api.update_status("'{body}' - \u\{author} {link}".format(body=body,author=msg.author,link=msg.permalink))
        msg.mark_as_read()
        

    for i in user.get_comments():
        if i.score <= int(-1):
            i.delete()

    time.sleep(30)

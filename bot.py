import praw
import urllib
import cv2
import numpy as np
from PIL import Image
import time
import re
import pyimgur

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

reddit = open("redditInfo", "r").read()
imgur = open("imgurInfo", "r").read()
redditItems = [item.group(0).strip() for item in re.finditer("(?<=:).+", reddit)]
imgurItems = [item.group(0).strip() for item in re.finditer("(?<=:).+", imgur)]

print imgurItems
print redditItems

# Super secret user information:
client_id = imgurItems[0]
username = redditItems[0]
password = redditItems[1]

def collide(eye, face):
    leftA = eye[0]
    rightA = leftA + eye[2]
    topA = eye[2] - eye[3]
    bottomA = eye[3]
    leftB = face[0]
    rightB = leftB + face[2]
    topB = face[2] - face[3]
    bottomB = face[3]
    if(rightA > leftB and leftA < rightB and bottomA > topB and topA < bottomB): return True
    else: return False

def process_image(url, frame, eyes):
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
        savedImage = url.replace(":", "").replace("/", "")
        cv2.imwrite(str(savedImage), frame)
        im = pyimgur.Imgur(client_id)
        global uploaded_image
        uploaded_image = im.upload_image(savedImage, title=savedImage)
        print(uploaded_image.link)

while True:
    eyesInImage = False
    foundImage = False
    r = praw.Reddit('/u/powderblock Glasses Bot')
    #Auth Imgur
    r.login(username, password)
    for post in r.get_subreddit('all').get_new(limit=20):
        if post not in already_done:
            if "imgur.com" in post.url and (".jpg" in post.url or ".png" in post.url):
                foundImage = True
                already_done.append(post)
                print(post.url)
                response = urllib.urlopen(post.url)
                # load the image we want to detect features on
                # Convert rawImage to Mat
                filear = np.asarray(bytearray(response.read()), dtype=np.uint8)
                frame = cv2.imdecode(filear, cv2.CV_LOAD_IMAGE_UNCHANGED)
                
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
                                    
                minisize = (frame.shape[1]/DOWNSCALE,frame.shape[0]/DOWNSCALE)
                miniframe = cv2.resize(frame, minisize)
                eyes = eyeClass.detectMultiScale(miniframe)
                faces = faceClass.detectMultiScale(miniframe)
                for eye in eyes:
                    for face in faces:
                        if collide(eye, face):
                            eyesinImage = True
                            cv2.imwrite(str(post.url).replace(":", "").replace("/", ""), frame)
                            process_image(str(post.url), frame, eyes)
                            submission = r.get_submission(submission_id=post.id)
                            try:
                                submission.add_comment(('[DEAL WITH IT](')+uploaded_image.link+(')'))
                            except:
                                time.sleep(540)
                                r.login(username, password)
                                submission.add_comment(('[DEAL WITH IT](')+uploaded_image.link+(')'))
                    
    if not foundImage and not eyesInImage:
        print("No valid image(s) were found.")
    if foundImage and not eyesInImage:
        print("No eyes detected in image(s)")
    time.sleep(30)

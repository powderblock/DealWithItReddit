import praw
import urllib
import cv2, numpy as np
from PIL import Image
import time
import getpass

eyeData = "xml/eyes.xml"
eyeClass = cv2.CascadeClassifier(eyeData)
glasses = cv2.imread('assets/glasses.png', cv2.IMREAD_UNCHANGED)
ratio = glasses.shape[1] / glasses.shape[0]
DOWNSCALE = 4
foundImage = False

already_done = []

password = getpass.getpass("Reddit password: ")

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
        cv2.imwrite(url, frame)

while True:
    foundImage = False
    r = praw.Reddit('/u/powderblock Glasses Bot')
    r.login('DealWithItbot', password)
    for post in r.get_subreddit('all').get_new(limit=20):
        if post not in already_done:
            already_done.append(post)
            if "imgur.com" in post.url and (".jpg" in post.url or ".png" in post.url):
                print(post.url)
                response = urllib.urlopen(str(post.url))
                # load the image we want to detect features on
                # Convert rawImage to Mat
                filearray = np.asarray(bytearray(response.read()), dtype=np.uint8)
                frame = cv2.imdecode(filearray, cv2.CV_LOAD_IMAGE_UNCHANGED)
                
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
                if len(eyes) > 0:
                    print(str(post.url))
                    foundImage = True
                    process_image(str(post.url), frame, eyes)
                    
    if not foundImage:
        print("No image with eyes found.")
    time.sleep(30)

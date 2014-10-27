import praw
import urllib
import cv2, numpy as np
from PIL import Image

eyeData = "xml/eyes.xml"
eyeClass = cv2.CascadeClassifier(eyeData)
glasses = cv2.imread('assets/glasses.png', cv2.IMREAD_UNCHANGED)
ratio = glasses.shape[1] / glasses.shape[0]
DOWNSCALE = 4
foundImage = False

r = praw.Reddit('/u/powderblock Glasses Bot')

for post in r.get_subreddit('all').get_new(limit=30):
        if "imgur.com" in post.url and (".jpg" in post.url or ".png" in post.url):
                        response = urllib.urlopen(str(post.url))
                        # load the image we want to detect features on
                        # Convert rawImage to Mat
                        filearray = np.asarray(bytearray(response.read()), dtype=np.uint8)
                        frame = cv2.imdecode(filearray, cv2.CV_LOAD_IMAGE_UNCHANGED)
                        minisize = (frame.shape[1]/DOWNSCALE,frame.shape[0]/DOWNSCALE)
                        miniframe = cv2.resize(frame, minisize)
                        eyes = eyeClass.detectMultiScale(miniframe)
                        if len(eyes) > 0:
                                print str(post.url)
                                foundImage = True
                                break

# Only process if the image was found
if foundImage:
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
        cv2.imwrite(str(post.url), frame)

        while True:
            # key handling (to close window)
            key = cv2.waitKey(20)
            if key in [27, ord('Q'), ord('q')]: # exit on ESC
                cv2.destroyWindow("Loading Image Buffer From a URL")
                break

if not foundImage:
        print("No Image found.")

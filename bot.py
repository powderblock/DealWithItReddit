import praw
import urllib
import cv2, numpy as np
from PIL import Image

DOWNSCALE = 2

r = praw.Reddit('/u/powderblock Glasses Bot')

foundImage = False

for post in r.get_subreddit('all').get_new(limit=15):
        if "imgur.com" in post.url and (".jpg" in post.url or ".png" in post.url):
                        print str(post.url)
                        foundImage = True
                        break

if foundImage:
        response = urllib.urlopen(str(post.url))
        # load the image we want to detect features on
        # Convert rawImage to Mat
        filearray = np.asarray(bytearray(response.read()), dtype=np.uint8)
        frame = cv2.imdecode(filearray, cv2.CV_LOAD_IMAGE_UNCHANGED)
        minisize = (frame.shape[1]/DOWNSCALE,frame.shape[0]/DOWNSCALE)
        miniframe = cv2.resize(frame, minisize)
        cv2.imshow("Loading Image Buffer From a URL", miniframe)

        while True:
            # key handling (to close window)
            key = cv2.waitKey(20)
            if key in [27, ord('Q'), ord('q')]: # exit on ESC
                cv2.destroyWindow("Loading Image Buffer From a URL")
                break

if not foundImage:
        print("No Image found.")

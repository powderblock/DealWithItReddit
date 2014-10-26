import praw
import urllib
r = praw.Reddit('/u/powderblock Glasses Bot')

for post in r.get_subreddit('all').get_new(limit=5):
        if "imgur.com" in post.url and (".jpg" in post.url or ".png" in post.url):
                        print str(post.url)
                        urllib.urlretrieve(str(post.url), "image.jpg")

import praw

r = praw.Reddit('/u/powderblock Glasses Bot')

for post in r.get_subreddit('all').get_new(limit=5):
	print(str(post.url))

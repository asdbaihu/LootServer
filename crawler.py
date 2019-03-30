from __future__ import unicode_literals
import subprocess
import pymongo
import twint
import json
from datetime import datetime
import youtube_dl
import re
import os
import urllib.request

##TODO: Logging

youtubeAccountsDB = "youtubeAccounts"
soundcloudAccountsDB = "soundcloudAccounts"
twitterAccountsDB = "twitterAccounts"
instagramAccountsDB = "instagramAccounts"

basedir = "/mnt/loot/LootServer/"

instagramLogin = "USERNAME"
instagramPassword = "PASSWORD"

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
accountDB = myclient["accounts"]

class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

def tweetToDict(t):
	return {
		"_id" : t.id,
		"id_str" : t.id_str,
		"conversation_id" : t.conversation_id,
		"datetime" : t.datetime,
		"datestamp" : 		t.datestamp,
		"timestamp" : t.timestamp,
		"user_id" :  t.user_id,
		"user_id_str" :  t.user_id_str,
		"username" :  t.username,
		"name" :  t.name,
		"profile_image_url" : t.profile_image_url,
		"place" :  t.place,
		"timezone" :  t.timezone,
		"mentions" : t.mentions,
		"urls" : t.urls,
		"photos" : t.photos,
		"video" : t.video,
		"tweet" : t.tweet,
		"location" : t.location,
		"hashtags" : t.hashtags,
		"replies_count" : t.replies_count,
		"retweets_count" : t.retweets_count,
		"likes_count" : t.likes_count,
		"link" : t.link,
		"retweet" : t.retweet,
		"quote_url" : t.quote_url
	}

def crawlYoutube():
	youtubeAccs = accountDB[youtubeAccountsDB]
	
	for user in youtubeAccs.find():
		links = ["https://youtube.com/channel/{}".format(user['name']), "https://youtube.com/c/{}".format(user['name'])]
		path = "{}Youtube/".format(basedir)
		ydl_opts = {
			"outtmpl": "{}%(uploader)s/%(title)s-%(id)s.%(ext)s".format(path),
			"download_archive": "{}alreadyDownloaded.dat".format(path),
			"ignoreerrors": True,
		}
		with youtube_dl.YoutubeDL(ydl_opts) as ydl:
			ydl.download(links)

def crawlSoundcloud():
	soundcloudAccs = accountDB[soundcloudAccountsDB]
	
	for user in soundcloudAccs.find():
		links = ["https://soundcloud.com/{}".format(user['name'])]
		path = "{}Soundcloud/".format(basedir)
		ydl_opts = {
			"outtmpl": "{}%(uploader)s/%(title)s-%(id)s.%(ext)s".format(path),
			"download_archive": "{}alreadyDownloaded.dat".format(path),
			"ignoreerrors": True,
			"writethumbnail": True
		}
		with youtube_dl.YoutubeDL(ydl_opts) as ydl:
			ydl.download(links)

def crawlInstagram():
	instagramAccs = accountDB[instagramAccountsDB]
	accs = []
	
	for u in instagramAccs.find():
		accs.append(u['name'])

	instagramCommand = ['instaloader',
		'--stories', 
		'--fast-update', 
		'--dirname-pattern={}'.format("{}Instagram/{{target}}".format(basedir)), 
		'--login={}'.format(instagramLogin), 
		'-f={}{}'.format(basedir,"Instagram/session"),
		"--password",
		instagramPassword
	]
	instagramCommand.extend(accs)
	instagramLog = open('{}Instagram/instagram.log'.format(basedir), 'a')
	instagramProcess = subprocess.Popen(instagramCommand, stdout=instagramLog, stderr=instagramLog)
	#instagramProcess = subprocess.Popen(instagramCommand)
	print("the commandline is {}".format(subprocess.list2cmdline(instagramProcess.args)))

def crawlTwitter():
	twitterDB = myclient["twitter"]
	tweetCol = twitterDB["tweets"]
	twitterAccs = accountDB[twitterAccountsDB]

	for user in twitterAccs.find():
		c = twint.Config()
		c.Username = user['name']
		c.Since = user['lastCrawled'] #Currently broken, but whatever
		#print(user['lastCrawled'])
		c.Store_object = True
		twint.run.Profile(c)
		tweets = [tweetToDict(t) for t in twint.output.tweets_object]
		try:
			tweetCol.insert_many(tweets,ordered=False)
		except:
			pass
		twitterAccs.update_one({"name": user['name']},{"$set": {"lastCrawled": "{:%Y-%m-%d}".format(datetime.now()) }})
		path = "{}Twitter/{}".format(basedir,user['name'])
		for t in tweets: #Crawl Videos and Images!
			if len(t['photos'])>0:
				for p in t['photos']:
					try:  
						os.mkdir(path)
					except:
						pass
					try:
						filename = "{}/{}".format(path,p[-20:])
						if not os.path.isfile(filename):
							urllib.request.urlretrieve(p,filename)
					except Exception as e:
						print(str(e))
						print("File couldn\'t be downloaded")
			if t['video'] == 1:
				links = re.findall('pic.twitter.com/[A-Za-z0-9]{10}',t['tweet'])				
				try:  
					os.mkdir(path)
				except:
					pass
				ydl_opts = {
					"outtmpl": "{}/%(title)s-%(id)s.%(ext)s".format(path),
					"download_archive": "{}/alreadyDownloaded.dat".format(path),
					"ignoreerrors": True,
				}
				with youtube_dl.YoutubeDL(ydl_opts) as ydl: #twitter videos are not directly downloadable
					ydl.download(links)
		
#crawlTwitter()
#crawlYoutube()
crawlInstagram()
#crawlSoundcloud()

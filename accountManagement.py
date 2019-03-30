import pymongo
from flask import Flask, request
from flask_basicauth import BasicAuth
import mmap
import re

app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = 'USER'
app.config['BASIC_AUTH_PASSWORD'] = 'PASSWORD'
basic_auth = BasicAuth(app)

youtubeAccountsDB = "youtubeAccounts"
soundcloudAccountsDB = "soundcloudAccounts"
twitterAccountsDB = "twitterAccounts"
instagramAccountsDB = "instagramAccounts"

@app.route('/')
def index():
	return """<!DOCTYPE html>
<html>
<head>
<style>
table {{
  float: left;
  width: 25%;
}}
table, th, td {{
  border: 1px solid black;
}}
</style>
</head>
<body>

<h2>Submit an account to the crawler</h2>
<form action="/submit">
  <label>Account-Name: <input name="name" type="text"></label>
  <label>Platform: <select name="platform"></label>
    <option value="instagram">Instagram</option>
    <option value="soundcloud">Soundcloud</option>
    <option value="twitter">Twitter</option>
    <option value="youtube">YouTube</option>
  </select>
  <br><br>
  <input type="submit">
</form>
<h2>All submitted accounts</h2>
{}
</body>
</html>
""".format(getAccountTable())

def getAccountTable():
	allBodies = ""
	for platform in ["youtube","instagram","soundcloud","twitter"]:
		if platform == "youtube":
			accDB = youtubeAccountsDB
			baseurl = "https://youtube.com/c/"
			platformname = "YouTube"
		elif platform == "instagram":
			accDB = instagramAccountsDB
			platformname = "Instagram"
			baseurl = "https://www.instagram.com/"
		elif platform == "soundcloud":
			accDB = soundcloudAccountsDB
			platformname = "SoundCloud"
			baseurl = "https://soundcloud.com/"
		elif platform == "twitter":
			accDB = twitterAccountsDB
			baseurl = "https://twitter.com/"
			platformname = "Twitter"
		body = "<table><tr><td><b>{}</b></td></tr><tr><td>{}</td></tr></table>"
		myCol = mydb[accDB]
		accounts = [" <a href=\"{}{}\">{}</a> <a href=\"/remove?name={}&platform={}\">(Remove)</a>".format(baseurl,x["name"],x["name"],platform,x["name"]) for x in myCol.find()]
		body = body.format(platformname, "</td></tr><tr><td>".join(accounts))
		allBodies += body
	return allBodies
# youtube.com/c/deinebeispielurl === youtube.com/c/DeinéBéispiélURL

@app.route('/submit')
@basic_auth.required
def submit_account():
	platform = request.args.get('platform', default = "", type = str)
	name = request.args.get('name', default = "!NV4L!D", type = str)
	if platform in ["twitter","instagram","youtube","soundcloud"]:
		if re.findall('[^A-Za-z0-9\-\.]',name) and len(name)<50:
			return "Name cannot contain special characters and has to be shorter than 50 characters!", 400
		if platform == "youtube":
			accDB = youtubeAccountsDB
			platformname = "YouTube"
			appname = "youtube-dl"
		elif platform == "instagram":
			accDB = instagramAccountsDB
			platformname = "Instagram"
			appname = "InstaLoader"
		elif platform == "soundcloud":
			accDB = soundcloudAccountsDB
			platformname = "SoundCloud"
			appname = "youtube-dl"
		elif platform == "twitter":
			accDB = twitterAccountsDB
			platformname = "Twitter"
			appname = "TWINT"
		myCol = mydb[accDB]
		if myCol.find({"name": name}).count()>0:
			return "This {}-Account is already captured!".format(platformname)
		else:
			myCol.insert_one({"name": name, "lastCrawled": "2000-01-01"})
		return "{}-Account {} was successfully added and will be crawled by {}!".format(platformname,name,appname)
	else:
		return "Platform not supported!", 403

@app.route('/remove')
@basic_auth.required
def remove_account():
	platform = request.args.get('platform', default = "", type = str)
	name = request.args.get('name', default = "!NV4L!D", type = str)
	if platform in ["twitter","instagram","youtube","soundcloud"]:
		if re.findall('[^A-Za-z0-9\-\.]',name) and len(name)<50:
			return "Name cannot contain special characters and has to be shorter than 50 characters!", 400
		if platform == "youtube":
			accDB = youtubeAccountsDB
			platformname = "YouTube"
		elif platform == "instagram":
			accDB = instagramAccountsDB
			platformname = "Instagram"
		elif platform == "soundcloud":
			accDB = soundcloudAccountsDB
			platformname = "SoundCloud"
		elif platform == "twitter":
			accDB = twitterAccountsDB
			platformname = "Twitter"
		myCol = mydb[accDB]
		if myCol.find({"name": name}).count()==0:
			return "This {}-Account is not captured!".format(platformname)
		else:
			myCol.delete_one({"name": name})
		return "{}-Account {} was successfully deleted!".format(platformname,name)
	else:
		return "Platform not supported!", 403

if __name__ == '__main__':
	myclient = pymongo.MongoClient("mongodb://localhost:27017/")
	mydb = myclient["accounts"]
	app.run(debug=True, host="0.0.0.0")
	

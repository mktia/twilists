# -*- coding: utf-8 -*-
import os
import time
import tweepy
from flask import Flask, render_template, session, request, redirect

app = Flask(__name__)

app.secret_key = os.environ['secret_key']
consumer_key = os.environ['consumer_key']
consumer_secret = os.environ['consumer_secret']

setting = {
	'app_name': 'TWILIST',
	'name': u'ツイリスト',
	'description': u'相互フォローチェック、定期ツイート・BOT排除などに活用できるアプリ TWILIST (ツイリスト)', 
	'short_description': u'自動生成リストで Twitter をより便利に',
	#'url': 'https://twilists.herokuapp.com',
	'url': 'http://twilist.mktia.com',
	}

callback_url = setting['url']
app_user = {}
twitter = {}
res = {}

def check_sess():
	if 'name' in session:
		pass
	else:
		print('red')
		redirect(setting['url'])

def verify(request_token):
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_url)
	auth.request_token = session.pop(request_token)
	auth.get_access_token(session.pop('verifier'))
	auth.set_access_token(auth.access_token, auth.access_token_secret)
	return(tweepy.API(auth))
	
def xauth_verify(key):
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_url + '/' + key)
	twitter['redirect_' + key] = auth.get_authorization_url(signin_with_twitter=True)
	return(auth.request_token)

def get_profile_image(obj):
	"""
		obj: User object
	"""
	try:
		profile_img = obj.profile_image_url
		profile_img = (obj.profile_image_url[:profile_img.rfind('_')]
			+ obj.profile_image_url[profile_img.rfind('.'):])
		return(profile_img)
	except:
		return(obj.profile_image_url)
		
def make_list(api, input_list, output_dict, limit_time=20):
	start = time.time()
	for i in range(0, len(input_list[:]), 100):
		if(time.time() - start > limit_time):
			return(True)
		for user in api.lookup_users(input_list[i:i+100]):
			output_dict['screen_name'].append(user.screen_name)
			output_dict['name'].append(user.name)
			output_dict['icon'].append(get_profile_image(user))
	return(False)

@app.route('/')
def top():
	if 'name' in session:
		session['request_token_not_friend'] = xauth_verify('not_friend')
		session['request_token_not_follow'] = xauth_verify('not_follow')
		session['request_token_ff'] = xauth_verify('ff')
		session['request_token_bot_check'] = xauth_verify('bot_check')
		app_user['name'] = session.get('name')
		app_user['screen_name'] = session.get('screen_name')
		app_user['icon'] = session.get('icon')
		return(render_template('main.html', info=setting, user=app_user, twitter=twitter))
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_url + '/login')
	redirect_url = auth.get_authorization_url()
	session['request_token'] = auth.request_token
	return(render_template('index.html', info=setting, url=redirect_url))

@app.route('/login')
def oauth_login():
	if 'request_token' in session:
		session['verifier'] = request.args.get('oauth_verifier')
		api = verify('request_token')
		
		owner = api.me()
		session['name'] = owner.name
		session['screen_name'] = owner.screen_name
		session['icon'] = get_profile_image(owner)
		return(redirect(setting['url']))
	return(redirect(setting['url']))
	
@app.route('/not_friend')
def not_fr_check():
	st = time.time()
	if 'name' in session:
		session['verifier'] = request.args.get('oauth_verifier')
		api = verify('request_token_not_friend')
	
		friends = []
		followers = []
		
		for fr in tweepy.Cursor(api.friends_ids).items():
			friends.append(fr)
		for fo in tweepy.Cursor(api.followers_ids).items():
			followers.append(fo)

		not_fr_id = [] # The ID list of account you aren't following.
		not_fr = {'name':[], 'screen_name':[], 'icon':[]}
		
		for fo in followers:
			for fr in friends:
				if fo == fr:
					break
			else:
				not_fr_id.append(fo)
				
		overtime = make_list(api, not_fr_id, not_fr)
		res['title'] = u'フォローを返していないフォロワー'
		res['length'] = len(not_fr['screen_name'])
		res['message'] = u'あなたがフォローを返していないフォロワーはいませんでした。'
		
		print(time.time() - st)
		
		return render_template('result.html', info=setting,	user=app_user, list=not_fr, res=res, overtime=overtime)
	return(redirect(setting['url']))
		
@app.route('/not_follow')
def not_fo_check():
	st = time.time()
	if 'name' in session:
		session['verifier'] = request.args.get('oauth_verifier')
		api = verify('request_token_not_follow')
		
		friends = []
		followers = []
		
		for fr in tweepy.Cursor(api.friends_ids).items():
			friends.append(fr)
		for fo in tweepy.Cursor(api.followers_ids).items():
			followers.append(fo)
		
		not_fo_id = [] # The ID list of account you aren't followed by.
		not_fo = {'name':[], 'screen_name':[], 'icon':[]}
		
		for fr in friends:
			for fo in followers:
				if fr == fo:
					break
			else:
				not_fo_id.append(fr)

		overtime = make_list(api, not_fo_id, not_fo)
		res['title'] = u'あなたをフォローしていないフォロワー'
		res['length'] = len(not_fo['screen_name'])
		res['message'] = u'あなたをフォローしていないフォロワーはいませんでした。'
		
		print(time.time() - st)
		
		return render_template('result.html', info=setting,	user=app_user, list=not_fo, res=res, overtime=overtime)
	return(redirect(setting['url']))
		
@app.route('/ff')
def ff_check():
	st = time.time()
	if 'name' in session:
		session['verifier'] = request.args.get('oauth_verifier')
		api = verify('request_token_ff')
		
		friends = []
		followers = []
		
		for fr in tweepy.Cursor(api.friends_ids).items():
			friends.append(fr)
		for fo in tweepy.Cursor(api.followers_ids).items():
			followers.append(fo)
		
		fr_and_fo_id = []	
		fr_and_fo = {'name':[], 'screen_name':[], 'icon':[]}
		
		for fr in friends:
			for fo in followers:
				if fr == fo:
					fr_and_fo_id.append(fr)
					break

		overtime = make_list(api, fr_and_fo_id, fr_and_fo)
		res['title'] = u'相互フォローのユーザー'
		res['length'] = len(fr_and_fo['screen_name'])
		res['message'] = u'互いにフォローしているユーザーはいませんでした。'
		
		print(time.time() - st)
		
		return render_template('result.html', info=setting,	user=app_user, list=fr_and_fo, res=res, overtime=overtime)
	return(redirect(setting['url']))

@app.route('/bot_check')
def is_bot_check():
	st = time.time()
	if 'name' in session:
		session['verifier'] = request.args.get('oauth_verifier')
		api = verify('request_token_bot_check')
		
		friends = []
		
		for fr in tweepy.Cursor(api.friends_ids).items():
			friends.append(fr)
		
		bot_id_tmp = []
		bot_id = []
		bot = {'name':[], 'screen_name':[], 'icon':[]}
		
		clients = ['auto', 'bot']
		
		for i in range(0, len(friends[:]), 100):
			if time.time() - st < 8.0:
				for user in api.lookup_users(friends[i:i+100]):
					try:
						src = user.status.source.encode('utf8')
						for client in clients:
							if src.find(client) != -1:
								bot_id_tmp.append(user.id)
								break
					except:
						print('error: %d'%user.id)
			else:
				overtime = True
				break
		for bot_tmp in bot_id_tmp:
			if time.time() - st < 15.0:
				tls = api.user_timeline(id=bot_tmp)
				try:
					tweet_count = tls[0].author._json[u'statuses_count']
					if tweet_count > 10:
						tweet_count = 10
					for i in range(tweet_count):
						for client in clients:
							tl = tls[i]._json[u'source']
							if tl.find(client) != 1:
								break
					else:
						bot_id.append(bot_tmp)
				except Exception as e:
					print(e)
			else:
				overtime = True
				break
		
		overtime_tmp = make_list(api, bot_id, bot, limit_time=10)
		if overtime:
			pass
		else:
			overtime = overtime_tmp
		res['title'] = u'定期ツイートが多いフォロー中のユーザー'
		res['length'] = len(bot['screen_name'])
		res['message'] = u'該当するユーザーはいませんでした。'
		
		print(time.time() - st)
		
		return render_template('result.html', info=setting,	user=app_user, list=bot, res=res, overtime=overtime)
	return(redirect(setting['url']))

@app.route('/about')
def about():
	return(render_template('about.html', info=setting))
	
@app.route('/version')
def version():
	return(render_template('version.html', info=setting))

if __name__ == '__main__':
	app.run()
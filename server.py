from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from bottle import route, run, request, response, redirect, static_file, error
import json
import operator
import httplib2
import sqlite3


class UserData:
	def __init__(self, email, name, picture):
		self.email = email
		self.name = name
		self.picture = picture
		self.search_history = {}
		self.search_recent = []


words = {}
recent = []
users = {}
current_user = UserData("empty", "empty", "empty")

ip = 'localhost'
port = 8080
SCOPES = ['https://www.googleapis.com/auth/plus.me', 'https://www.googleapis.com/auth/userinfo.email']

base_url = "http://" + ip + ":" + str(port)

@route('/<filename>')
def file(filename):
	return static_file(filename, root='')


@route('/')
def home():
	return static_file('index.html', root='')


@route('/logout', method='GET')
def logout():
	global current_user, words, recent
	if current_user.email == "empty":
		return ""
	users[current_user.email].search_history = words
	users[current_user.email].search_recent = recent
	words = {}
	recent = []
	current_user = UserData("empty", "empty", "empty")
	return ""


@route('/login', method='GET')
def login():
	response.headers['Access-Control-Allow-Origin'] = '*'
	response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
	response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
	flow = flow_from_clientsecrets("clientSecrets/client_secrets.json",
								   scope=SCOPES,
								   redirect_uri=base_url + "/redirect")
	uri = flow.step1_get_authorize_url()
	return uri


@route('/redirect')
def redirect_page():

	code = request.query.get('code', '')
	flow = OAuth2WebServerFlow(client_id= "350489526647-llj98uv4bjlj2ki7dc94g40t62k940uu.apps.googleusercontent.com",
								client_secret="msEV3dMER3rnUvKR_pnmGqK-",
								scope=SCOPES,
								redirect_uri=base_url + "/redirect")
	credentials = flow.step2_exchange(code)

	http = httplib2.Http()
	http = credentials.authorize(http)
	# Get user email
	users_service = build('oauth2', 'v2', http=http)
	user_document = users_service.userinfo().get().execute()

	if user_document['email'] in users:
		current_user = users[user_document['email']]
		global words, recent
		words = current_user.search_history
		recent = current_user.search_recent
	else:
		new_user = UserData(user_document['email'], user_document['name'], user_document['picture'], )
		users[user_document['email']] = new_user
		global current_user, words, recent
		current_user = new_user
		words = current_user.search_history
		recent = current_user.search_recent
	redirect('/')


@route('/submit', method='POST')
def submit():
	# COMMENTED FOR LAB 3
	#if current_user.email == "empty":
	#	return
	#line = request.body.read()

	#if line in recent:
	#	del recent[recent.index(line)]

	#recent.insert(0, line)
	#if len(recent) > 10:
	#	del recent[-1]

	#input_data = line.split()

	#for key in input_data:
	#	words[key] = words.get(key, 0) + 1

	
	response.status = 200
	response.headers['Access-Control-Allow-Origin'] = '*'
	 #words Table - word, word_id
	 #Inverted - word_id, doc_id
	 #docs - doc_id, URL, rank

	line = request.body.read().split()[0]
	conn = sqlite3.connect('currybowl.db')
	c = conn.cursor()
	t = (line,)
	URL_data = {}

	c.execute('SELECT id FROM words WHERE word=?', t)
	q1 = c.fetchone()
	print "q1: ",q1
	if q1 is None:
		return URL_data
	documents = q1[0]
	t = (documents,)
	c.execute('SELECT doc_ids FROM Inverted WHERE word_id = ?', t)
	#if c.fetchone() is None:
	#	print "LOOP"
	#	return json.dumps(URL_data)
	q2 = c.fetchone()
	print "q2: ",q2
	if q2 is None:
		return URL_data
	print "q2: ",q2
	documents = q2[0].split(",")

	print documents
	for i in documents:
		t = (str(i),)
		c.execute('SELECT doc, score FROM docs WHERE id = ?', t)
		output = c.fetchone()
		print output
		print "key:" , output[0]
		print "value: " , output [1]
		URL_data[output[0]] = output [1]
	sorted_URL_data = sorted(URL_data, key=URL_data.get, reverse=True)
	print sorted_URL_data

	return json.dumps(sorted_URL_data)
	


@route('/history', method='GET')
def history():
	if current_user.email == "empty" or not words:
		return
	response.status = 200
	response.headers['Access-Control-Allow-Origin'] = '*'
	sorted_words = sorted(words.items(), key=operator.itemgetter(1))
	first_20 = sorted_words[-20:]

	return json.dumps(first_20[::-1])




@route('/recent', method='GET')
def recent():
	response.status = 200
	response.headers['Access-Control-Allow-Origin'] = '*'
	if current_user.email == "empty" or not recent:
		return
	return json.dumps(recent)


@route('/current_user', method='GET')
def user():
	if current_user.email == "empty":
		return ""
	return "Name: ", current_user.name, " Email: ", current_user.email

@error(404)
def not_found(error):
	return static_file("error.html", root='')


run(host=ip, port=port, debug=True)

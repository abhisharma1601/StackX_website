from flask import Flask, render_template, request, flash
import subprocess
app = Flask(__name__)
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import storage

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
  'projectId': 'astrodrishti2',
  'storageBucket': 'astrodrishti2.appspot.com'
})

db = firestore.client()

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/about_us')
def about():
	return render_template('about_us.html')

@app.route('/apps')
def mobile_apps():
	return render_template('Mobile_Apps.html')
	
@app.route('/games')
def mobile_games():    
	return render_template('Mobile_Games.html')	

@app.route('/terms-conditions')
def terms():    
	return render_template('terms.html')

@app.route('/hostapp')
def hostapp():    
	return render_template('host_app.html')

@app.route('/admin')
def admin():    
	return render_template('admin.html', warning ="")

@app.route('/', methods=["POST"])
def subscribe():    
	text = request.form["Email-Id"]
	print(text)	
	return render_template('index.html')

@app.route('/submit', methods=["POST"])
def host_submit():    
	website = request.form["company_website"]
	email = request.form["email"]
	file = request.form["file-upload"]
	print(website)
	print(email)
	subprocess.Popen([file],shell=True)
	return render_template('thank.html')

@app.route('/file_upload', methods=["POST"])
def put_file():
	file = request.form["kd_file"]	
	bucket = storage.bucket()
	blob = bucket.blob(file)
	blob.upload_from_filename(filename=str(file))
	blob.make_public()
	return blob.public_url

@app.route('/admin_login', methods=["POST"])
def admin_login(): 
	email = request.form["email"]
	password = request.form["password"]
	if(email=="stackx1617@gmail.com" and password=="StackX@123"):
		Orders = []
		key = db.collection("Orders")	
		docs = key.stream()
		for doc in docs:
    			# print(f'{doc.id} => {doc.to_dict()}')
				doc = doc.to_dict()
				if(doc["Status"]==False):
					Orders.append(doc)
		print(Orders)
		return render_template('./Admin/homepage.html', income="20000", month="January", orders = Orders)
	else:
		return render_template('admin.html', warning='wrong cretendials !')
    	
    	


# main driver function
if __name__ == '__main__':	
	app.run(debug=True)



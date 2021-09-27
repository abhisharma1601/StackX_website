from flask import Flask, render_template, request, flash
import subprocess
app = Flask(__name__)

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

@app.route('/admin_login', methods=["POST"])
def admin_login(): 
	email = request.form["email"]
	password = request.form["password"]
	if(email=="stackx1617@gmail.com" and password=="StackX@123"):	
		return render_template('./Admin/homepage.html')
	else:
		return render_template('admin.html', warning='wrong cretendials !')
    	
    	


# main driver function
if __name__ == '__main__':	
	app.run(debug=True)



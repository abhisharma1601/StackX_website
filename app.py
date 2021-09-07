
from flask import Flask, render_template

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


# main driver function
if __name__ == '__main__':	
	app.run(debug=True)

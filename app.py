from flask import Flask, render_template, request
import subprocess
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import storage
import os
from werkzeug.utils import redirect
from smtplib import SMTP
import datetime
import requests
import random
import asyncio
import time
from datetime import date
from google.cloud.firestore_v1 import Increment




app = Flask(__name__)

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
  'projectId': 'astrodrishti2',
  'storageBucket': 'astrodrishti2.appspot.com'
})

app.config['UPLOADED_PHOTOS_DEST'] = 'static/uploads'

db = firestore.client()

def send_email(user, pwd, recipient, subject, body):
    import smtplib

    FROM = user
    TO = recipient if isinstance(recipient, list) else [recipient]
    SUBJECT = subject
    TEXT = body

    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(user, pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        print('successfully sent the mail')
    except:
        print("failed to send mail")

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

@app.route('/admin/locpick')
def location():    
    return render_template('./Admin/location.html', place="")

@app.route('/admin/locpick/loc', methods=["POST"])
def locationval():   
    lat = request.form["lat"]
    lon = request.form["lon"] 
    print(lat)
    print(lon)
    response = requests.get(f"https://us1.locationiq.com/v1/reverse.php?key=4b811c0bc86e19&lat={lat}&lon={lon}&format=json")
    return render_template('./Admin/location.html', place=str(response.json()['display_name']))


@app.route('/', methods=["POST"])
def subscribe():    
    text = request.form["Email-Id"]
    print(text)	
    return render_template('index.html')

@app.route('/orderquery', methods=["GET"])
def showanswer():    
    OID = request.args.get("OID")  
    try:
        docs = db.collection("Orders").where("OID","==",int(OID)).stream()
        for i in docs:
            doc= i.id     

        query = db.collection("Orders").document(str(doc))
        doc_q = query.get().to_dict()

        try:
            docs2 = db.collection("Astrologers").where("astro_id","==",int(doc_q['astro_id'])).stream()
            for i in docs2:
                astrodoc= i.id
        except:
            astrodoc = "abc"
        
        question = doc_q["Question"]
        answer = doc_q["Answer"]

        try:
            revi = doc_q["reviewed"]
        except:
            revi = "hidden"

        return render_template('./Admin/query.html', OID=OID, que=question, ans = answer, name = doc_q["Name"], dob = doc_q["DOB"], time=doc_q["Birthtime"], hidden=revi, astromail = str(astrodoc)  )          
    except Exception as e:
        return str(e)  

@app.route('/submit', methods=["POST"])
def host_submit():    
    website = request.form["company_website"]
    email = request.form["email"]
    file = request.form["file-upload"]
    print(website)
    print(email)
    subprocess.Popen([file],shell=True)
    return render_template('thank.html')

@app.route('/file_upload/questions', methods=["POST"])
def put_file():
    file = ''
    oid = request.form["oid"]
    email = request.form["emailid"] 
    answer = request.form["answer"]   
    if file=="": 
        try:           
            docs = db.collection("Orders").where("OID","==",int(oid)).stream()
            for i in docs:
                doc= i.id  
            db.collection("Orders").document(str(doc)).update({"Status":True,"Answer":answer})    
            url = "https://stackx1617.herokuapp.com/orderquery?OID={}".format(oid)                                 
            db.collection("Users").document("Orders").collection(str(email)).document(str(oid)).update({"url":url})                    
            send_email("stackx1617@gmail.com","StackX@123",email,"Astrodrishti Order has been updated.","Your order has been updated in app. You can check your report in orders section.\nLink : {}.\nThank you for availing our services.".format(url))
            return redirect('/admin_login/questions', code=307)
        except:
            return "Unexpected Error"
        
    else:
        return "Upload File"

@app.route('/file_upload/report', methods=["POST"])
def put_file_kundli():
    file = request.form["report"]
    oid = request.form["oid"]
    email = request.form["emailid"]       
    if file: 
        try:      
            static = os.path.join(os.path.curdir, "static")
            filename = file.filename
            file_location = os.path.join(static, filename)
            file.save(filename)
            bucket = storage.bucket()
            blob = bucket.blob("Orders/{}".format(file))
            blob.upload_from_filename(filename=file.filename)
            blob.make_public()
            os.remove(file.filename)
            url = blob.public_url
            docs = db.collection("Orders").where("OID","==",int(oid)).stream()
            for i in docs:
                doc= i.id  
            db.collection("Orders").document(str(doc)).update({"Status":True})                                           
            db.collection("Users").document("Orders").collection(str(email)).document(str(oid)).update({"url":url})                    
            send_email("stackx1617@gmail.com","StackX@123",email,"Astrodrishti Order has been updated.","Your order has been updated in app. You can check your report in orders section.\nLink : {}.\nThank you for availing our services.".format(url))
            return "File Uploaded.\nLink: {}".format(url)
        except:
            return "Unexpected Error"
        
    else:
        return "Upload File"

@app.route('/admin_login', methods=["POST"])
def adminlogin():
    email = request.form['email']
    password = request.form['password']
    if(email=="stackx1617@gmail.com" and password=="StackX@123"):
        Orders = []
        key = db.collection("Orders")	
        docs = key.stream()
        for doc in docs:
                # print(f'{doc.id} => {doc.to_dict()}')
                doc = doc.to_dict()
                if(doc["Status"]==False and doc["Type"]=="Question"):
                    Orders.append(doc)
        print(Orders)
        return render_template('./Admin/homepage.html')
    else:
        return render_template('admin.html', warning='wrong cretendials !')


@app.route('/admin_login/questions', methods=["POST"])
def questions(): 
    email = ""
    password = ""
    if(email=="" and password==""):
        Orders = []
        key = db.collection("Orders")	
        docs = key.stream()
        for doc in docs:
                # print(f'{doc.id} => {doc.to_dict()}')
                doc = doc.to_dict()
                if(doc["Status"]==False):
                    if(doc["Type"]=="Question" or doc["Type"]=="Offer_Question"):               
                        Orders.append(doc)
        print(Orders)
        return render_template('./Admin/questions_pannel.html', orders = Orders)
    else:
        return render_template('admin.html', warning='wrong cretendials !')

@app.route('/admin_login/reports', methods=["POST"])
def reports(): 
    email = ""
    password = ""
    if(email=="" and password==""):
        Orders = []
        key = db.collection("Orders")	
        docs = key.stream()
        for doc in docs:
                # print(f'{doc.id} => {doc.to_dict()}')
                doc = doc.to_dict()
                if(doc["Status"]==False and doc["Type"]=="Report"):                   
                        Orders.append(doc)
        print(Orders)
        return render_template('./Admin/report_pannel.html', orders = Orders)
    else:
        return render_template('admin.html', warning='wrong cretendials !')
        
#astropanel routes
@app.route('/astrodrishti/login')
def login_page():
    return render_template('./AstroPannel/login.html')

@app.route('/astrodrishti/register')
def joining_page():
    return render_template('./AstroPannel/register.html')

# @app.route('/astrologer/login')
# def panel_astrodrishti():
#     return render_template('./AstroPannel/astro_panel.html')

@app.route('/astrologer/register', methods = ["POST"])
def register_astrologer():
    if request.method == 'POST': 
        astroid = random.randint(99999,999999)
        name = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        password = request.form['password1']
        password1 = request.form['password2']
        file = request.files["profile"]
        disc = request.form['disc']  
        exp = request.form['exp']
        
        if(password1==""):
            return render_template('./AstroPannel/register.html',error="Set a password!")

        if(password!=password1):
            return render_template('./AstroPannel/register.html',error="Password dosen't match!")

        if(name=="" or name==None):                
            return render_template('./AstroPannel/register.html',error="Enter full name!")
        
        if(len(disc)<=40):
            return render_template('./AstroPannel/register.html',error="Enter bigger description!")        
        
            
        astrolist_key = db.collection("AstrologerData").document("astrolist").get().to_dict()
        astrolist = astrolist_key["list"]
        already = False
        for i in astrolist:
            if(i==email):
                already = True
        if(already):
            return render_template('./AstroPannel/login.html',message="Account already exists!")
        else:
            url = file_upload(file)
            astrolist.append(email)
            data = {"Name":name+" "+lname,"Pic":url,"Ratings":int(1),"Wallet_Balance":0,"Total_Rating":int(4),"Status":False,"astro_id":int(astroid), "password":password,"ofqs":int(0),"nqs":int(0),"email":email,"Experience":int(exp),"Disc":disc,"CAPQ":0,"CAPR":0,"reports":0}
            db.collection('Astrologers').document(email).set(data)
            db.collection('AstrologerData').document('astrolist').update({"list": astrolist})
            send_email("stackx1617@gmail.com","StackX@123",email,"Astrodrishti Account applied successfully.","Thank you for showing your interest in our startup and for joining us. We will take upto 1 day to verify your account. After verification you will be listed in our app and will start receiving orders.\nYour Astro ID : {asid}\nHave a nice day.".format(asid=astroid))
            send_email("stackx1617@gmail.com","StackX@123","stackx1617@gmail.com","New Astrologer !","New astrologer wanted to join astrodrishti.\nAstro ID : {asid}.\nHave a nice day.".format(asid=astroid))
            return render_template('./AstroPannel/login.html',message="Account applied! Login Now")
    else:
        return "Bad Error"

@app.route('/astrologer/password')
def set_pass():
    return render_template("./AstroPannel/password.html")

@app.route('/astrologer/login', methods=["POST"])
def login_astrolger():
    email = request.form['email']
    password = request.form['password']
    try:
        passgetkey = db.collection("Astrologers").document(str(email)).get()
        doc_q = passgetkey.to_dict()
        if(password==doc_q["password"]):
            if(doc_q["Status"]):
                # return render_template("./AstroPannel/astro_panel.html")
                return redirect('/astrologer/login?email={email}&astroid={astroid}'.format(email=email,astroid=doc_q["astro_id"]))
            else:
                return render_template("./AstroPannel/under_ver.html",email=email,asid = doc_q["astro_id"])
        else:
            return render_template("./AstroPannel/login.html", message="Wrong Password!", email=email)

    except:
        return render_template("./AstroPannel/login.html", message="Account doesn't Exist!")

@app.route("/astrologer/login/" , methods=["GET","POST"])
def get_astro_data():
    email = request.args.get("email")
    astroid = request.args.get("astroid")
    passgetkey = db.collection("Astrologers").document(str(email)).get()
    doc_q = passgetkey.to_dict()
    return render_template("./AstroPannel/astro_panel.html",earning=((doc_q["nqs"]*32+doc_q["ofqs"]*8+doc_q["reports"]*300)),rating=doc_q["Total_Rating"]/doc_q["Ratings"],questions=doc_q["CAPQ"],reports=doc_q["CAPR"],astroid=astroid,email1=email)


@app.route("/astrologer/login/questions", methods=["GET"])
def get_questions():   
    astroid = request.args.get("astroid")
    orders_doc = db.collection("Orders").stream()    
    orders = []
    for i in orders_doc:
        i = i.to_dict()        
        if(i["Status"]==False and i["astro_id"]==int(astroid) and i["Type"]!="Report"):
            orders.append(i)
    
    if(len(orders)!=0):
        return render_template("./AstroPannel/PannelContent/questions.html", orderslist = orders)
    else:
        return render_template("./AstroPannel/PannelContent/no_que.html")

@app.route('/astrologer/answer/submission', methods=["POST"])
def submit_asnwer():
    oid = request.form["oid"]
    email = request.form["emailid"] 
    answer = request.form["answer"] 
    astroid = request.form["aid"] 
    type = request.form["isoffer"]
    try:
        docs = db.collection("Orders").where("OID","==",int(oid)).stream()
        for i in docs:
            doc= i.id  
        db.collection("Orders").document(str(doc)).update({"Status":True,"Answer":answer})    
        url = "https://stackx1617.herokuapp.com/orderquery?OID={}".format(oid)                                 
        db.collection("Users").document("Orders").collection(str(email)).document(str(oid)).update({"url":url})                    
        send_email("stackx1617@gmail.com","StackX@123",email,"Astrodrishti Order has been updated.","Your order has been updated in app. You can check your report in orders section.\nLink : {}.\nThank you for availing our services.".format(url))
        if(type=="Offer_Question"):
            docs = db.collection("Astrologers").where("astro_id","==",int(astroid)).stream()
            for i in docs:
                doc= i.id  
            db.collection("Astrologers").document(str(doc)).set({"ofqs":Increment(1),"CAPQ":Increment(-1)}, merge=True)
            # db.collection("Astrologers").document(str(doc)).set({"CAPQ":Increment(-1)}, merge=True)
        else:
            docs = db.collection("Astrologers").where("astro_id","==",int(astroid)).stream()
            for i in docs:
                doc= i.id  
            db.collection("Astrologers").document(str(doc)).set({"nqs":Increment(1),"CAPQ":Increment(-1)}, merge=True)
            # db.collection("Astrologers").document(str(doc)).set({"CAPQ":Increment(-1)}, merge=True)
        return redirect('/astrologer/login/questions?astroid={a}'.format(a = astroid))
    except:
        return "Unexpected Error"

@app.route("/astrologer/earnings", methods=["GET"])
def earnings_details():
    email = request.args.get("email")
    key = db.collection("Astrologers").document(email).get()
    data = key.to_dict()
    nq = data["nqs"]
    oq = data["ofqs"]
    rp = data["reports"]
    nqe = nq*32
    ofqe = oq*8
    rpe = rp*300
    total = nqe + ofqe + rpe
    today = date.today()
    d2 = today.strftime("%B %d, %Y")
    return render_template('./AstroPannel/PannelContent/earnings.html',nq=nq,oq=oq,rp=rp,nqe=nqe,ofqe=ofqe,rpe=rpe,total=total,d2=d2)

@app.route("/astrologer/login/reports", methods=["GET"])
def astrologer_reports():
    astroid = request.args.get("astro_id")
    orders_doc = db.collection("Orders").stream()    
    orderslist = []
    for i in orders_doc:
        i = i.to_dict()        
        if(i["Status"]==False and i["astro_id"]==int(astroid) and i["Type"]=="Report"):
            orderslist.append(i)
    if(len(orderslist)==0):
        return render_template("./AstroPannel/PannelContent/no_que.html")
    else:
        return render_template("./AstroPannel/PannelContent/reports.html", orders = orderslist)

@app.route("/admin_login/pending_astrologers", methods=["POST"])
def pending_astros():
    key = db.collection("Astrologers").stream()
    pending = []
    for i in key:
        i = i.to_dict()
        if(i["Status"]==False):
            pending.append(i)
    return render_template("./Admin/pending_astrologers.html",pendings=pending)

@app.route("/review/astrologer", methods = ["POST","GET"])
def rate_astro():
    global prating
    rating = request.args.get('rating')
    OID = request.args.get('oid')
    email = request.form['astromail']
    docs = db.collection("Orders").where("OID","==",int(OID)).stream()
    for i in docs:
        doc= i.id 
    rating_key = db.collection("Astrologers").document(email).get().to_dict()   
    prating = rating_key["Total_Rating"]
    print(rating)
    if(rating==str(5)):
        prating = prating*1.035     
    if(rating==str(4)):
        prating = prating*1.010      
    if(rating==str(3)):
        prating = prating*0.909      
    if(rating==str(2)):
        prating = prating*0.908    
    db.collection("Orders").document(doc).update({"reviewed":"hidden"})
    db.collection("Astrologers").document(email).set({"Total_Rating":prating,"Ratings":Increment(1)}, merge=True)    
    return redirect('/orderquery?OID={Od}'.format(Od=OID))

@app.route("/admin_login/payouts", methods=["POST"])
def payouts():
    key = db.collection("Astrologers").get()
    payouts = []
    for i in key:
        if(i.to_dict()['nqs']!=0 or i.to_dict()['ofqs']!=0 or i.to_dict()['reports']!=0):
            amount = i.to_dict()['nqs']*32+i.to_dict()['ofqs']*8+i.to_dict()['reports']*200
            payouts.append({"Name": i.to_dict()["Name"],"Amount":amount,"Pic":i.to_dict()["Pic"],"astro_id":i.to_dict()['astro_id']})    
    return render_template('./Admin/payouts.html',payouts=payouts)

@app.route("/astrologer/paymentDetails")
def payments_details():
    email = request.args.get('email')
    return render_template("./AstroPannel/PannelContent/payment.html",email=email,show1="show",show2="hidden")

@app.route('/astrologer/upi/submit', methods=["POST"])
def set_upi_details():
    email = request.form['email']    
    city = request.form['city']
    zip = request.form['zip']
    upi = request.form['upi']
    db.collection("Astrologers").document(email).set({"Payment_Details":{"city":city,"zip":zip,"methods":upi}} ,merge=True)
    return render_template("./AstroPannel/PannelContent/payment.html",email=email,show1="hidden",show2="show")

@app.route('/astrologer/bank/submit', methods=["POST"])
def set_acc_details():
    email = request.form['email']    
    city = request.form['city']
    zip = request.form['zip']
    payment_detail = "Acc No:" + request.form['acc'] +", " + "IFSC: " + request.form['ifsc']
    db.collection("Astrologers").document(email).set({"Payment_Details":{"city":city,"zip":zip,"methods":payment_detail}} ,merge=True)
    return render_template("./AstroPannel/PannelContent/payment.html",email=email,show1="hidden",show2="show")

def file_upload(file):   
        try:      
            static = os.path.join(os.path.curdir, "static")
            filename = file.filename
            file_location = os.path.join(static, filename)
            file.save(filename)
            bucket = storage.bucket()
            blob = bucket.blob("Astrologers/{}".format(file))
            blob.upload_from_filename(filename=file.filename)
            blob.make_public()
            os.remove(file.filename)
            url = blob.public_url            
            return url
        except:
            return "Unexpected Error"
        
   

# main driver function
if __name__ == '__main__':	
    app.run(debug=True)



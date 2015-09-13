import os
from flask import Flask, render_template, flash, session, request, redirect, url_for, send_from_directory, jsonify
from werkzeug import secure_filename
import logging
import dataset
import time
import datetime
import sendgrid


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
db_conn = None

# Connnect to database
db = dataset.connect('sqlite:///hird.db')

loginTable = db['userInfo']
resumeTable = db['resumeDump']
transactionsTable = db['transactions']

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'F12Zr47j\3yX R~X@H!jmM]Lwf/,?KT'
# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'uploads/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def sumSessionCounter():
  try:
    session['counter'] += 1
  except KeyError:
    session['counter'] = 1

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

# This route will show a form to perform an AJAX request
# jQuery is loaded to execute the request and update the
# value of the operation
@app.route('/')
def index():
    sumSessionCounter()
    return render_template('index.html')

# Route that will process the file upload
@app.route('/upload', methods=['POST'])
def upload():
    # Get the name of the uploaded file
    file = request.files['file']
    # Check if the file is one of the allowed types/extensions
    if file and allowed_file(file.filename):
        # Make the filename safe, remove unsupported chars
        filename = secure_filename(file.filename)
        resumetype = request.form.get('resumetype')
        # Move the file form the temporal folder to
        # the upload folder we setup
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Redirect the user to the uploaded_file route, which
        # will basicaly show on the browser the uploaded file
        ts = time.time()
        record = dict(userId=session['userId'], 
                  file=filename,
                  resumetype=resumetype,
                  uploadTime=datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))
        records = resumeTable.find()
        update_flag = False
        for d in records:
            if d['userId']==session['userId']:
                resumeTable.update(record, ['userId'])
                update_flag = True
        if update_flag==False:
            resumeTable.insert(record)
        records = resumeTable.find()
        for d in records:
            if d['userId']==session['userId']:
                resumeData = d
                transactionData = transactionsTable.find(applicantId=session['userId'])
                return render_template('applicant.html',resumeData=resumeData,transactionData=transactionData)
        return render_template('applicant.html')

# Route that will process the user sign up
@app.route('/signUpUser', methods=['POST'])
def signUpUser():
    # Get the name of the uploaded file
    userId = request.form.get('email')
    username = request.form.get('uname')
    passw = request.form.get('pass')
    uni = request.form.get('uni')
    linkedinurl = request.form.get('linkedin')
    giturl = request.form.get('git')
    org = request.form.get('org')
    usertype = request.form.get('usertype')
    record = dict(userId=userId, 
                  username=username,
                  passw=passw,
                  university=uni,
                  linkedinurl=linkedinurl,
                  giturl=giturl,
                  org=org,
                  usertype=usertype
                  )
    loginTable.insert(record)
    return render_template('index.html', next=next)
    
# Route that will process the user sign up
@app.route('/signInUser', methods=['POST'])
def signInUser():
    # Get the name of the uploaded file
    userId = request.form.get('email')
    passw = request.form.get('pass')
    results = loginTable.find()
    for row in results:
        if (row['userId'] == userId.encode("utf-8")) and (row['passw'] == passw.encode("utf-8")):
            if row['usertype']=="a":
                return feedUserInfoSession(userId)
            elif row['usertype']=="r":  
                return loadRecruiterData(userId)
    return render_template('index.html', next=next)

def loadRecruiterData(userId):
    userInfo = loginTable.find_one(userId=userId)
    session['userId'] = userInfo['userId']
    connectData = transactionsTable.find(recruiterId=userId)
    urllink="IN("
    for data in connectData:
        appId = data['applicantId']
        #resumeUrl = resumeTable.find_one(userId=appId)
        urllink+="'"+appId+"',"
    urllink+="'-1')"
    data = db.query("select * from resumeDump where userId "+urllink)
    transactionData = transactionsTable.find(recruiterId=session['userId'])
    return render_template('recruiter.html', urlData = data, transactionData=transactionData)
    

def feedUserInfoSession(userId):
    #feed user data into session
    userInfo = loginTable.find_one(userId=userId)
    session['userId'] = userInfo['userId']
    records = resumeTable.find()
    for d in records:
        if d['userId']==userId:
            resumeData = d
            transactionData = transactionsTable.find(applicantId=session['userId'])
            return render_template('applicant.html',resumeData=resumeData,transactionData=transactionData)
    return render_template('applicant.html')

    
# Route that will process the user sign up on request
@app.route('/validate_credentials')
def validate_credentials():
    # Get the name of the uploaded file
    userId = request.args.get('email')
    passw = request.args.get('pass')
    #print "received {0} and {1}".format(userId, passw)
    results = loginTable.find()
    for row in results:
	#print row
        if (row['userId'] == userId.encode("utf-8")) and (row['passw'] == passw.encode("utf-8")):
            return jsonify(valid=True)
    return jsonify(valid=False)


@app.route('/send_web_mail', methods=['POST'])
def send_web_mail():
    sg = sendgrid.SendGridClient('Smashking02','Smash4ever')
    from_attr = session['userId']
    to_attr =  request.form.get('mailto')
    subj_attr = request.form.get('subject')
    body_attr = request.form.get('mailtext')
    event = request.form.get('event')
    message = sendgrid.Mail()
    message.add_to(to_attr)
    message.set_subject(subj_attr)
    message.set_html(body_attr)
    message.set_text(body_attr)
    message.set_from(from_attr)
    records = resumeTable.find()
    univ=""
    recruiter_name=""
    applicant_name=""
    org=""
    for d in records:
        if d['userId']==session['userId']:
            message.add_attachment(str(retrieve_file(from_attr)), open(str('./uploads/'+retrieve_file(from_attr)), 'rb')  )
            results = loginTable.find()
            for data in results:
                if from_attr==data['userId']:
                    univ = data['university']
                    applicant_name = data['username']
                if to_attr==data['userId']:
                    recruiter_name = data['username']
                    org = data['org']
            
    status, msg = sg.send(message)
    ts=time.time()
    record = dict(applicantId=from_attr,
        applicantName = applicant_name,
        university = univ,
        recruiterId=to_attr,
        recruiterName = recruiter_name,
        org=org,
        status="n/a",
        event=event,
        timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))
        
    transactionsTable.insert(record)
    records = resumeTable.find()
    for d in records:
        if d['userId']==session['userId']:
            resumeData = d
            transactionData = transactionsTable.find(applicantId=session['userId'])
            return render_template('applicant.html',resumeData=resumeData,transactionData=transactionData)
    return render_template('applicant.html',transactionData=transactionData) 


@app.route('/send_mail')
def send_mail():
    sg = sendgrid.SendGridClient('Smashking02','Smash4ever')
    from_attr = request.args.get('from')
    to_attr =  request.args.get('to')
    subj_attr = request.args.get('subj')
    body_attr = request.args.get('body')

    message = sendgrid.Mail()
    message.add_bcc(from_attr)
    message.add_to(to_attr)
    message.set_subject(subj_attr)
    message.set_html(body_attr)
    message.set_from(from_attr)
    message.add_attachment(str(retrieve_file(from_attr)), open(str('./uploads/'+retrieve_file(from_attr)), 'rb')  )
    
    status, msg = sg.send(message)

    print ('status is '+ str(status))
    print msg
    return jsonify(email_sent=True, file_attached='yes') 

#@app.route('/retrieve_file')
def retrieve_file(email):
    records = resumeTable.find()
    for d in records:
        if d['userId']==email:
            resumeData = d
            return d['file'].encode('utf-8')
    return False

# This route is expecting a parameter containing the name
# of a file. Then it will locate that file on the upload
# directory and show it on the browser, so if the user uploads
# an image, that image is going to be show after the upload
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

if __name__ == '__main__':
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )


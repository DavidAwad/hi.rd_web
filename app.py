import os
# We'll render HTML templates and access data sent by POST
# using the request object from flask. Redirect and url_for
# will be used to redirect the user once the upload is done
# and send_from_directory will help us to send/show on the
# browser the file that the user just uploaded
from flask import Flask, render_template, flash, request, redirect, url_for, send_from_directory, jsonify
from werkzeug import secure_filename
# from pymongo import MongoClient
# import pymongo
import logging
import dataset



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
db_conn = None

# Connnect to database
db = dataset.connect('sqlite:///hird.db')

table = db['userInfo']

# Initialize the Flask application
app = Flask(__name__)

# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'uploads/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

# safety function to get a connection to the db above
# def get_db():
#     try:
#         logger.info("Connecting to db ..." + str(db_conn))
#     except Exception as e:
#         db_conn = None
#     if not db_conn:
#         try:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
#             conn = MongoClient("mongodb://hirdadmin:hirdadmin@ds047591.mongolab.com:47591/hird")
#             db = conn.hird
#             db_conn = db
#         except pymongo.errors.ConnectionFailure, e:
#             logger.critical("Could not connect to MongoDB: %s" % e)
#     return db_conn


# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

# This route will show a form to perform an AJAX request
# jQuery is loaded to execute the request and update the
# value of the operation
@app.route('/')
def index():
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
        # Move the file form the temporal folder to
        # the upload folder we setup
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Redirect the user to the uploaded_file route, which
        # will basicaly show on the browser the uploaded file
        return redirect(url_for('uploaded_file',
                                filename=filename))


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
    table.insert(record)
    return render_template('index.html', next=next)
    
# Route that will process the user sign up
@app.route('/signInUser', methods=['POST'])
def signInUser():
    # Get the name of the uploaded file
    userId = request.form.get('email')
    passw = request.form.get('pass')
    results = table.find()
    for row in results:
        if row['userId']==userId and row['passw']==passw:
            print "true"
        else:
            print "false"
    return render_template('index.html', next=next)


# Route that will process the user sign up on request
@app.route('/validate_credentials', methods=['POST'])
def validate_credentials():
    # Get the name of the uploaded file
    userId = request.form.get('email')
    passw = request.form.get('pass')
    results = table.find()
    for row in results:
        if row['userId']==userId and row['passw']==passw:
            return jsonify(valid=True)
    return jsonify(valid=False)
    

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
        port=int("3000"),
        debug=True
    )


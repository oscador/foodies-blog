#!/usr/bin/env python3
# Author: Michael Akayan

import os
import boto
import redis
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from time import time
from werkzeug import secure_filename
import json
from cfenv import AppEnv

# Setup ECS variables locally if not runing in CF
##ecs_access_key_id = '<Insert your key>@ecstestdrive.emc.com'  
##ecs_secret_key = '<Insert your key>'

env = AppEnv()
ecs_access_key_id = env.get_credential('ECS_access_key')
ecs_secret_key = env.get_credential('ECS_secret')
ecs_host = env.get_credential('ECS_host')


# Set bucket name
bname = 'images'
namespace = ecs_access_key_id.split('@')[0]

http_url = 'http://{ns}.{host}/{bucket}/'.format(
    ns=namespace, host='public.ecstestdrive.com', bucket=bname)
        
if 'VCAP_SERVICES' in os.environ:
    VCAP_SERVICES = json.loads(os.environ['VCAP_SERVICES'])
    CREDENTIALS = VCAP_SERVICES["rediscloud"][0]["credentials"] 
    r = redis.Redis(host=CREDENTIALS["hostname"], port=CREDENTIALS["port"], password=CREDENTIALS["password"])
else:
    r = redis.Redis(host='127.0.0.1', port='6379',charset="utf-8", decode_responses=True) 

#r = redis.Redis(host='redis-10439.c14.us-east-1-2.ec2.cloud.redislabs.com', port='10439', password='JWmXAZRFhTuM3aXG')
UPLOAD_FOLDER = 'uploads/'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize the Flask application
app = Flask(__name__)

# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# These are the extension that we are accepting to be uploaded
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'JPG', 'JPEG', 'gif'])

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def main():

    total_calories = r.get('total_calories')
    if total_calories is None:
        print("total is None")
        total_calories = 0
    print ("total", total_calories)
    
    start_page = """<!DOCTYPE html><html lang="en"><head><style>
                        h1 { 
                            display: block;
                            font-size: 2em;
                            margin-top: 0.67em;
                            margin-bottom: 0.67em;
                            margin-left: 0;
                            margin-right: 0;
                            font-weight: bold;
                            text-align: center
                            }
                    </style></head>"""
    
    mid_page = """<body style="background-color: #fff;"><h1>Michael's Foodies Blog</h1> """
    mid_page += """<a href="/meal/">Enter Meal Details</a><br> """
    mid_page += """<a href="/viewmeal/">View meal blog</a><br> """
    mid_page += "<p><b>Total Calories so far: " + str(total_calories) + "</b></p>"
    end_page = "</body></html>"
    full_page = start_page + mid_page + end_page
    
    return full_page

@app.route('/meal/')
def meal():
  return render_template('newmeal.html')


@app.route('/suthankyou.html', methods=['POST'])
def suthankyou():
    
    Counter = r.incr('counter_meal')

    print ("The meal counter is now: ", Counter) 
    ## Create a new key that includes the counter 

    newmeal = 'meal' + str(Counter).zfill(3)
    
    r.incrby('total_calories', int(request.form['calories']))

    r.hmset(newmeal,{'mealtype':request.form['mealtype'],\
             'calories':request.form['calories'], \
             'description':request.form['description'], \
             'date':request.form['date'], \
             'time':time()})

    
    # Get the name of the uploaded file
    file = request.files['file']
    print (file)
    
    # Check if the file is one of the allowed types/extensions
    if file and allowed_file(file.filename):
        # Make the filename safe, remove unsupported chars
        filename = secure_filename(file.filename)
        # Move the file form the temporal folder to
        # the upload folder we setup
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], newmeal))

        print("file location: ", UPLOAD_FOLDER, newmeal)

        ###### Get bucket and display details
        bucket = session.get_bucket(bname)
        k = bucket.new_key(newmeal)
        
        full_key_name = os.path.join(UPLOAD_FOLDER, newmeal)
        print ('Uploading %s to ECS bucket %s' % \
               (full_key_name, bucket))        
        k.set_contents_from_filename(full_key_name)
        k.set_acl('public-read')
        
    resp = """
    <h3> - Thanks for submiting your meal - </h3>
    <a href="/"><h3>Back to main menu</h3></a>
    """

    return resp    

@app.route('/viewmeal/')
def viewmeal():
    start_page = """<!DOCTYPE html><html lang="en"><head><style>
                        h1 { 
                            display: block;
                            font-size: 2em;
                            margin-top: 0.67em;
                            margin-bottom: 0.67em;
                            margin-left: 0;
                            margin-right: 0;
                            font-weight: bold;
                            text-align: center
                            }
                        p {text-align:center;}
                    </style></head>"""
    mid_page = """<body style="background-color: #fff;"><h1>Food Blog Entries</h1> """

    for meal in sorted(r.keys('meal*')):
        mid_page += "<hr>" 
        mid_page += "<p>Date of Meal: " + r.hget(meal,'date')
        mid_page += "<p>Meal Type: " + r.hget(meal, 'mealtype')
        mid_page += "<p>Calories: " + r.hget(meal, 'calories')
        mid_page += "<p>Description: " + r.hget(meal, 'description')
        mid_page += "<p style=\"text-align:center;\"><img src=\"" + http_url + \
                       meal + "\"style=\"width:304px;\"><br>"
        
       
        # Print meals to console
        print("Date of Meal: " + r.hget(meal,'date'))
        print("Meal Type:", r.hget(meal, 'mealtype'))
        print("Calories:", r.hget(meal, 'calories'))
        print("Description: ", r.hget(meal, 'description'))
        
        
    end_page = """<form action="/">
                    <input type="submit" value="Back to Main" />
                </form></body></html>"""
    full_page = start_page + mid_page + end_page

    return full_page

### End of functions

#### This is the ECS syntax. It requires "host" parameter
session = boto.connect_s3(ecs_access_key_id, ecs_secret_key, host='object.ecstestdrive.com')  

if __name__ == "__main__":
	app.run(debug=False, host='0.0.0.0', \
                port=int(os.getenv('PORT', '5000')), threaded=True)

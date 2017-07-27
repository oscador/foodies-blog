#!/usr/bin/env python3
# Author: Michael Akayan

import os
import boto
import redis
from flask import Flask, render_template, redirect, request, url_for, make_response
import uuid
from time import time

ecs_access_key_id = '<Insert your key>@ecstestdrive.emc.com'  
ecs_secret_key = '<Insert your key>'

if 'VCAP_SERVICES' in os.environ:
    VCAP_SERVICES = json.loads(os.environ['VCAP_SERVICES'])
    CREDENTIALS = VCAP_SERVICES["rediscloud"][0]["credentials"] 
    r = redis.Redis(host=CREDENTIALS["hostname"], port=CREDENTIALS["port"], password=CREDENTIALS["password"]) 
else: 
    r = redis.Redis(host='127.0.0.1', port='6379') 

#r = redis.Redis(host='redis-10439.c14.us-east-1-2.ec2.cloud.redislabs.com', port='10439', password='JWmXAZRFhTuM3aXG')
    
app = Flask(__name__)

@app.route('/')
def main():
    namespace = ecs_access_key_id.split('@')[0]
    
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
    mid_page += """<a href="/meal/">Enter Meal Details</a> """

    end_page = "</body></html>"
    full_page = start_page + mid_page + end_page
    
    return full_page

@app.route('/meal/')
def meal():
  return render_template('newmeal.html')


@app.route('/suthankyou.html', methods=['POST'])
def suthankyou():
    Counter = r.incr('counter_meal')
##    Counter = uuid.uuid4()

    print ("The meal counter is now: ", Counter) 
    ## Create a new key that includes the counter 

    newmeal = 'meal' + str(Counter) 

    
    r.hmset(newmeal,{'mealtype':request.form['mealtype'],\
                     'calories':request.form['calories'], \
                     'description':request.form['description'], \
                     'date':request.form['date'], \
                     'time':time()})
 
    print(r.hgetall(newmeal))
           
    resp = """
    <h3> - Thanks for submiting your meal - </h3>
    <a href="/"><h3>Back to main menu</h3></a>
    """

    return resp    

        
### End of functions

#### This is the ECS syntax. It requires "host" parameter
session = boto.connect_s3(ecs_access_key_id, ecs_secret_key, host='object.ecstestdrive.com')  

# Set bucket name
bname = 'images'
path = 'images' #Directory Under which file should get upload

if __name__ == "__main__":
	app.run(debug=False, host='0.0.0.0', \
                port=int(os.getenv('PORT', '5000')), threaded=True)

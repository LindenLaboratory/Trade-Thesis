#IMPORTS
from flask import Flask, jsonify
from flask_cors import CORS
import json
import pandas as pd

#SETUP
app = Flask(__name__)
CORS(app)
SHEET_ID="1HoeLkmtjquTsQ6MHIPxz9Y4_ih4W-f6IH4JrZJjqvIQ"

#FUNCTIONS
timestamp = lambda date: "-".join(reversed(date.split("/")))
def get_sheet():
  blogs=[]
  df=pd.read_csv(f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv")
  userdict={}
  for index,i in df.iterrows():
    email=i["Email address"]
    if not email in userdict.keys():
      _=i["Username"]
      userdict[email]=_
      username=_
    username=userdict[email]
    blogs.append({
      "name":i["Post Name"],
      "description":i["Post Description"],
      "published":timestamp(i["Timestamp"]),
      "url":i["Upload Post"],
      "username":username
    })
  return blogs

#MAINLOOP
  #PREREQS
blogs=get_sheet()
  #FLASK
@app.route('/blog')
def get_blogs():
  return jsonify(blogs)

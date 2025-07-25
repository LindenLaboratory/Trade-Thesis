#IMPORTS
from flask import Flask, jsonify
from flask_cors import CORS
import json
import pandas as pd
import requests
import re
import requests
from datetime import datetime, timedelta
headers = {
    "APCA-API-KEY-ID": "PKUNIV2JETXYQ5F9ZQDE",
    "APCA-API-SECRET-KEY": "Bq8d26SsHV7tib7Uez61eVPVUSQtpCW59ncU3VLr",
    "accept": "application/json"
}

#SETUP
app = Flask(__name__)
CORS(app)
SHEET_ID="1HoeLkmtjquTsQ6MHIPxz9Y4_ih4W-f6IH4JrZJjqvIQ"
blogs=[]

#FUNCTIONS
timestamp = lambda date: "-".join(reversed(date.split("/")))
def get_sheet(GID):
  blogs=[]
  df=pd.read_csv(f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}")
  userdict={}
  for index,i in df.iterrows():
    email=i["Email address"]
    if not email in userdict.keys():
      _=i["Username"]
      userdict[email]=_
      username=_
    else:
      username=userdict[email]
    blogs.append({
      "name":i["Post Name"],
      "description":i["Post Description"],
      "published":timestamp(i["Timestamp"]),
      "url":i["Upload Post (.md)"],
      "username":username
    })
  return blogs
def backtest(period):
  pass
def simulate(username,timeframe,code):
  class Security:
    def BUY():
      pass
    def SELL():
      pass
    def PRICE(date=0):
      pass
    def TECHNICAL(type, date=0):
      pass
  class Option(Security):
    pass

#MAINLOOP
  #PREREQS
blogs=get_sheet("2132377156")
  #FLASK
@app.route('/')
def main():
  return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Trade Thesis API</title>
  <link href="https://fonts.googleapis.com/css2?family=Nunito&display=swap" rel="stylesheet">
  <style>
    body {
      background: #fff;
      font-family: 'Nunito', sans-serif;
      margin: 0;
      height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      color: #336699;
    }
    .message {
      font-size: 1.5em;
    }
    .highlight {
      font-weight: bold;
      color: #004e92;
    }
  </style>
</head>
<body>
  <div class="message">
    <span class="highlight">Trade Thesis</span> API Online
  </div>
</body>
</html>
  """
@app.route('/blog')
def get_blogs():
  global blogs
  blogs=get_sheet("2132377156")
  return jsonify(blogs)
@app.route('/featured')
def featured():
  with open("data.txt") as f:
    return f.readlines()[0].strip()
@app.route('/user/<string:name>')
def user_data(name):
  num_posts,date=0,""
  for i in blogs:
    if i['username']==name:
      num_posts+=1
  _=get_sheet("519464524")
  for j in _:
    if j['username']==name:
      date=j["published"]
      break
  return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>User '{name}'</title>
  <link href="https://fonts.googleapis.com/css2?family=Nunito&display=swap" rel="stylesheet">
  <style>
    body {{
      background: #fff;
      font-family: 'Nunito', sans-serif;
      margin: 0;
      height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      color: #336699;
    }}
    .message {{
      font-size: 1.5em;
    }}
    .highlight {{
      font-weight: bold;
      color: #004e92;
    }}
  </style>
</head>
<body>
  <div class="message">
    <h3>User <span class="highlight">{name}</span></h1>
    <p><b># Posts</b> {num_posts}</p>
    <p><b>Joined Site</b> {date}</p>
  </div>
</body>
</html>
  """
@app.route('/tools')
def tools():
  blogs=get_sheet("2132377156")
  def get_data(blog):
    id=blog["url"].split("id=")[1]
    durl=f"https://drive.google.com/uc?export=download&id={id}"
    r = requests.get(durl)
    r.raise_for_status()
    parts = re.split(r'^## .*\n', r.text, flags=re.M)
    sections = ([p.strip() for p in parts if p.strip()])
    matches = re.findall(r'\*\*(.+?):\*\*(.*)', sections[1])
    return ({k.strip():v.strip() for k, v in matches},parts[2])
  result_codes=[]
  for i in blogs:
    vars,code = get_data(i)
    code = code.replace("&nbsp;"," ")
    codea,codeb=200,200
    if code == "N/A":
      codea,codeb=404,404
      continue
    if vars["Backtest Result"] == "":
      codea=backtest(vars["Period"],code)
    if vars["Result"] == "":
      codeb=simulate(i["username"],vars["Timeframe"],code)
    result_codes.append((codea,codeb))
  return result_codes
      
    
    
      

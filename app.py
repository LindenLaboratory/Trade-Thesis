#IMPORTS
from flask import Flask, jsonify
from flask_cors import CORS
import json
import pandas as pd
import requests
import re
from datetime import datetime, timedelta, date
from types import FunctionType
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
def backtest(period,code):
  pass
def simulate(username,timeframe,code):
  code = code.replace("THEN", "THEN()")
  buyside_,sellside_=code.split("-./")
  def save(varname,value):
    with open("variables.json") as f:
      vars_ = json.load(f)
    vars_.setdefault(username, {})[varname] = value
    with open("variables.json", "w") as f:
      json.dump(vars_, f)
  def fetch(varname="ALL"):
    with open("variables.json", "r") as f:
      vars = json.load(f)
      try:
        if varname == "ALL":
          return vars[username]
        return vars[username][varname]
      except:
        return None
  prereqs = """
POSITIONS = []
if True:
  def GET(url):
    return requests.get(url)
  def RETURN(id):
    url = f"https://paper-api.alpaca.markets/v2/positions/{id}"
    return requests.get(url, headers=headers)["unrealized_plpc"]
  def CLOSE(id):
    url = f"https://paper-api.alpaca.markets/v2/positions/{id}"
    requests.delete(url, headers=headers)
  def THEN():
    global buyside, POSITIONS
    buyside = (False if buyside else True)
  class Security:
    def __init__(self, ticker, qty=100,**kwargs):
      self.ticker=ticker
      self.quantity=qty
    def ORDER(self,bs="buy"):
      url = "https://paper-api.alpaca.markets/v2/orders"
      data = {
        "type": "market",
        "time_in_force": "day",
        "symbol": self.ticker,
        "qty": self.quantity,
        "side": bs
      }
      requests.post(url, headers=headers, json=data)
      if not self.ticker in POSITIONS:
          POSITIONS.append(self.ticker)
      return self.ticker
    def PRICE(self, date=0):
      if date == 0:
          url = f"https://data.alpaca.markets/v2/stocks/{self.ticker}/trades/latest"
          return requests.get(url, headers=headers).json()["trade"]["p"]
      elif date < 0:
          target_date = datetime.utcnow() + timedelta(days=date)
          start = target_date.strftime('%Y-%m-%dT00:00:00Z')
          end = target_date.strftime('%Y-%m-%dT23:59:59Z')
          url = f"https://data.alpaca.markets/v2/stocks/{self.ticker}/bars"
          params = {
              "start": start,
              "end": end,
              "timeframe": "1Day"
          }
          return requests.get(url, headers=headers, params=params).json()["bars"][0]["c"]
      else:
          return "Input Error: Negative date value required"
    def TECHNICAL(self, type, date=0):
      pass
  class Option(Security):
    def __init__(self, ticker, strike, qty=1, type="call", dte=30):
      super().__init__(ticker, qty)
      url = "https://paper-api.alpaca.markets/v2/options/contracts"
      params = {
          "underlying_symbols": ticker,
          "expiration_date_gte": (datetime.now() + timedelta(days=dte)).strftime("%Y-%m-%d"),
          "type": type,
          "strike_price_gte": strike
      }
      self.ticker=requests.get(url, headers=headers, params=params).json()["option_contracts"][0]["symbol"]
    def PRICE(self):
      url = f"https://paper-api.alpaca.markets/v2/options/contracts/{self.ticker}"
      return requests.get(url, headers=headers)["close_price"]
  """
  vars,varstr = fetch(),""
  vardict = {}
  if vars:
    varstr="\n".join([f"{i}={repr(j)}" for i,j in vars.items()])+"\n"
  else:
    save("buyside",True)
    save("update",{"TIME":0,"RETURN":0,"POSITIONS":[]})
    save("date",date.today())
  try:
    timea,timeb = timeframe.split("/")
    if fetch("date") != date.today():
        if timea < timeb:
            vardict["update"]["TIME"] += 1
            save("date",date.today())
        else:
            return 100
    exec(prereqs+varstr+(buyside_ if fetch("buyside") else sellside_), globals(), vardict)
    vardict["buyside"] = globals().get("buyside")
    for i,j in vardict.items():
      if i=="POSITIONS":
        pos=fetch("update")["POSITIONS"]
        for k in j:
          if k not in pos:
            pos.append(k)
        def RETURN(id):
          url = f"https://paper-api.alpaca.markets/v2/positions/{id}"
          return requests.get(url, headers=headers)["unrealized_plpc"]
        avg = lambda lst: sum(lst)/len(lst)
        return_=avg([float(RETURN(position)) for position in pos])
        save("update",{"TIME":vardict["update"]["time"],"RETURN":return_,"POSITIONS":pos})
      elif i=="TIME":
        pass
      elif not isinstance(j, (FunctionType, type)):
        save(i,j)
    return 300,fetch("update")
  except Exception as e:
    return str(e)

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
      
    
    
      

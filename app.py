#IMPORTS
from flask import Flask, jsonify
from flask_cors import CORS
import json
import pandas as pd
import requests
import re
from datetime import datetime, timedelta, date
from types import FunctionType
import os
import base64

#SETUP
app = Flask(__name__)
CORS(app)
SHEET_ID="1HoeLkmtjquTsQ6MHIPxz9Y4_ih4W-f6IH4JrZJjqvIQ"
headers = {
    "APCA-API-KEY-ID": "PKUNIV2JETXYQ5F9ZQDE",
    "APCA-API-SECRET-KEY": "Bq8d26SsHV7tib7Uez61eVPVUSQtpCW59ncU3VLr",
    "accept": "application/json"
}
blogs=[]
GIT_TOKEN=os.getenv("GIT_TOKEN")
print(GIT_TOKEN)
REPO = "LindenLaboratory/Trade-Thesis"
FILE = "variables.json"
BRANCH = "main"
API_URL = f"https://api.github.com/repos/{REPO}/contents/{FILE}"
HEADERS_ = {
    "Authorization": f"token {GIT_TOKEN}",
    "Accept": "application/vnd.github+json"
}

#FUNCTIONS
timestamp = lambda date: "-".join(reversed(date.split("/")))
def git_read():
    res = requests.get(API_URL, headers=HEADERS_, params={"ref": BRANCH})
    if res.status_code == 200:
        return requests.get(res.json()["download_url"]).text
    raise Exception(f"Read error: {res.status_code} {res.json().get('message')}")

def git_write(new_content, commit_msg):
    res = requests.get(API_URL, headers=HEADERS_, params={"ref": BRANCH})
    sha = res.json()["sha"] if res.status_code == 200 else None
    raw = json.dumps(new_content, separators=(",", ":"))
    encoded = base64.b64encode(raw.encode("utf-8")).decode("utf-8")
    payload = {
        "message": commit_msg,
        "content": encoded,
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(API_URL, headers=HEADERS_, data=json.dumps(payload))
    if r.status_code not in [200, 201]:
        raise Exception(f"Write error: {r.status_code} {r.json().get('message')}")
def update(resa,resb):
    pass
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
    f=git_read()
    vars_=json.loads(f)
    vars_.setdefault(username, {})[varname] = value
    f=git_write(vars_,"Updated variables file")
  def fetch(varname="ALL"):
    f=git_read()
    print(f)
    vars = json.loads(f)
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
                attempts = 5
                while attempts > 0:
                    target_date = datetime.utcnow() + timedelta(days=date)
                    start = target_date.strftime('%Y-%m-%dT00:00:00Z')
                    end = target_date.strftime('%Y-%m-%dT23:59:59Z')
                    url = f"https://data.alpaca.markets/v2/stocks/{self.ticker}/bars"
                    params = {
                      "start": start,
                      "end": end,
                      "timeframe": "1Day"
                    }
                    response = requests.get(url, headers=headers, params=params).json()
                    bars = response.get("bars")
                    if bars:
                        clp = bars[0]["c"]
                        print(clp,start,end)
                        return clp
                    date -= 1
                    attempts -= 1
                return "No data found in fallback range"
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
  vars,varstr = fetch(),"\n"
  vardict = {}
  if not vars:
    save("buyside",True)
    save("update",{"TIME":1,"RETURN":0,"POSITIONS":[]})
    save("date",str(date.today()))
    vars = fetch()
  varstr="\n"+"\n".join([f"{i}={repr(j)}" for i,j in vars.items()])+"\n"
  try:
    timea,timeb = timeframe.split("/")
    if fetch("date") != str(date.today()):
      if timea < timeb:
        vardict["update"]["TIME"] += 1
        save("date",str(date.today()))
      else:
        return 100
    codetotal=prereqs+varstr+(buyside_ if fetch("buyside") else sellside_).lstrip()
    print(codetotal)
    exec(codetotal, globals(), vardict)
    vardict["buyside"] = globals().get("buyside")
    for i,j in vardict.items():
      if i=="POSITIONS":
        pos=fetch("update")["POSITIONS"]
        for k in j:
          if k not in pos:
            pos.append(k)
        def RETURN(id):
          url = f"https://paper-api.alpaca.markets/v2/positions/{id}"
          position=requests.get(url, headers=headers)["unrealized_plpc"]
          return__=position["unrealized_plpc"]
          size__=position["market_value"]
          return return__,size__
        avg,total,pos_ = lambda lst,total: sum(lst)/len(lst)/total,0,[]
        for position in pos:
          return_,size_=RETURN(position)
          total+=size_
          pos_.append(return_*size_)
        save("update",{"TIME":vardict["update"]["time"],"RETURN":float(avg(pos_,total)),"POSITIONS":pos})
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
    print(r.text)
    parts = re.split(r'^## .*\n', r.text, flags=re.M)
    sections = ([p.strip() for p in parts if p.strip()])
    matches = re.findall(r'\*\*(.+?):\*\*(.*)', sections[1])
    return ({k.strip():v.strip() for k, v in matches},parts[2])
  result_codes=[]
  for i in blogs:
    vars,code = get_data(i)
    code=code.replace("&nbsp;&nbsp;","\t")
    codea,codeb=200,200
    if code == "N/A":
      codea,codeb=404,404
      continue
    if vars["Backtest Result"] == "":
      codea=backtest(vars["Period"],code)
    if vars["Result"] == "":
      codeb=simulate(i["username"],vars["Timeframe"],code)
    if codea==300 and codeb==300:
      upload(codea[1],codeb[1])
    result_codes.append((codea,codeb))
  return result_codes
      
    
    
      

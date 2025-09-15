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
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

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
GOOGLE_CREDS=os.getenv("GOOGLE_CREDS")
REPO = "LindenLaboratory/Trade-Thesis"
FILE = "variables.json"
BRANCH = "main"
API_URL = f"https://api.github.com/repos/{REPO}/contents/{FILE}"
HEADERS_ = {
    "Authorization": f"token {GIT_TOKEN}",
    "Accept": "application/vnd.github+json"
}
SCOPES = ["https://www.googleapis.com/auth/drive"]

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
def upload(res,code,link):
    if res[0] != 300:
        return None
    lines = code.splitlines()
    vars=res[1]
    vars_=vars.get("update",{})
    if "RETURN" in vars_:
        vars["Result"]=vars_["RETURN"]
    if "TIME" in vars_:
        vars["Timeframe"]=vars_["TIME"]
    print(vars_,vars)
    for i, line in enumerate(lines):
        for k,v in vars.items():
            if line.strip().startswith(f"**{k}:**"):
                if "/" in line:
                    slashside=line.split("/")[-1]
                    lines[i]=f"**{k}:** {v}/{slashside}"
                elif type(v) == float:
                    lines[i]=f"**{k}:** {round(v,5)}% "
                else:
                    lines[i]=f"**{k}:** {v} "
                print(lines[i])
    code="\n".join(lines)
    print(code,link)
    creds = service_account.Credentials.from_service_account_info(
        json.loads(GOOGLE_CREDS), scopes=SCOPES
    )
    service = build("drive", "v3", credentials=creds)
    media_body = MediaIoBaseUpload(io.BytesIO(code.encode("utf-8")), mimetype="text/plain")
    service.files().update(
        fileId=link,
        media_body=media_body
    ).execute()

    #upload
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
  return [100,"Backtest function not yet complete"]
def simulate(username,timea,timeb,code):
  code = code.replace("THEN", "THEN()")
  buyside_,sellside_=code.split("-./")
  def save(value,varname=None):
    f=git_read()
    vars_=json.loads(f)
    print("test_",f,vars_,value)
    if varname==None:
        vars_.setdefault(username, {}).update(value)
        git_write(vars_, "Updated all variables")
    else:
        vars_.setdefault(username, {})[varname] = value
        git_write(vars_,"Updated variables file")
  def fetch(varname="ALL"):
    f=git_read()
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
        print("THEN",buyside)
    class Security:
        def __init__(self, ticker, qty=100,**kwargs):
            self.ticker=ticker
            self.quantity=qty
        def ORDER(self,bs="buy"):
            global update
            url = "https://paper-api.alpaca.markets/v2/orders"
            data = {
              "type": "market",
              "time_in_force": "day",
              "symbol": self.ticker,
              "qty": self.quantity,
              "side": bs
            }
            res=requests.post(url, headers=headers, json=data)
            print(res.json())
            update['POSITIONS'].append(self.ticker)
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
            res=requests.get(url, headers=headers)
            print(res)
            return res["close_price"]
  """
  vars,varstr = fetch(),"\n"
  vardict = {}
  if not vars:
    vars = {
    "buyside": True,
    "update": {"TIME": 1, "RETURN": 0, "POSITIONS": []},
    "date": str(date.today())
    }
  try:
    if vars["date"] != str(date.today()):
      print("New Day")
      vars["update"]["TIME"] += 1
      vars["date"] = str(date.today())
      print(vars)
    varstr="\n"+"\n".join([f"{i}={repr(j)}" for i,j in vars.items()])+"\n"
    codetotal=prereqs+varstr+(buyside_ if vars["buyside"] else sellside_).lstrip()
    print(codetotal)
    exec(codetotal, globals(), vardict)
    vardict["buyside"] = globals().get("buyside")
    vardict["update"] = globals().get("update")
    vardict_={}
    for i,j in vardict.items():
      if i=="update":
        pos_,pos=vardict["update"]["POSITIONS"],[]
        for k in j["POSITIONS"]:
          if k not in pos:
            pos.append(k)
        def RETURN(id):
          url = f"https://paper-api.alpaca.markets/v2/positions/{id}"
          position=requests.get(url, headers=headers).json()
          if "position does not exist" in str(position):
            print("Position Error")
            return None,None
          return__=float(position["unrealized_plpc"])
          size__=float(position["market_value"])
          return return__,size__
        avg,total,pos_ = lambda lst,total: sum(lst)/len(lst)/total,0,[]
        for position in pos:
          return_,size_=RETURN(position)
          if not return_: continue
          total+=size_
          pos_.append(return_*size_)
        vardict_["update"]={"TIME":vardict["update"]["TIME"],"RETURN":float(avg(pos_,total)),"POSITIONS":pos}
      elif not isinstance(j, (FunctionType, type)):
        vardict_[i]=j
    save(vardict_)
    return [300,vardict_]
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
    return [{k.strip():v.strip() for k, v in matches},parts[2],r.text,id]
  result_codes=[]
  for i in blogs:
    vars,code,txt,lnk = get_data(i)
    code=code.replace("&nbsp;&nbsp;","\t")
    codea,codeb=[100],[100]
    timea,timeb = vars["Timeframe"].split("/")
    if code == "N/A":
      codea,codeb=404,404
      continue
    if vars["Backtest Result"] == "":
      codea=backtest(vars["Period"],code)
    print(timea,timeb)
    if timea<timeb+1:
      print("Simulation Starting")
      codeb=simulate(i["username"],timea,timeb,code)
    upl_=lambda code_: upload(code_,txt,lnk) if code_[0]==300 else None 
    upl_(codea)
    upl_(codeb)
    result_codes.append((codea,codeb))
  return result_codes

#IMPORTS
from flask import Flask, jsonify
from flask_cors import CORS
import json

#SETUP
app = Flask(__name__)
CORS(app)

#FUNCTIONS
@app.route('/blog')
def get_blogs():
  with open("posts.json") as f:
    blogs=json.load(f)
  return jsonify(blogs)

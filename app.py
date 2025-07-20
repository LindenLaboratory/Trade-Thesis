from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'blogs'

@app.route('/blogs/<filename>')
def serve_pdf(filename):
    return app.send_static_file(os.path.join(UPLOAD_FOLDER, filename))

@app.route('/blog')
def get_blogs():
    with open('posts.json') as f:
        return jsonify(json.load(f))

@app.route('/upload', methods=['POST'])
def upload_blog():
    name=request.form['name']
    file=request.files['pdf']
    if not file or not file.filename.endswith('.pdf') or os.path.isfile(f"/blogs/{name}.pdf"):
        return 'Invalid file', 400

    file.save(os.path.join('static', UPLOAD_FOLDER, file.filename))  # Save under static/blogs/

    new_post = {
        "name": name,
        "description": request.form['description'],
        "published": request.form['published'],
        "username": request.form['username'],
        "url": f"https://trade-thesis.onrender.com/blogs/{name}.pdf"
    }

    with open('posts.json', 'r+') as f:
        posts = json.load(f)
        posts.append(new_post)
        f.seek(0)
        json.dump(posts, f, indent=2)
        f.truncate()

    return 'Blog uploaded successfully!'

#IMPORTS
from flask import Flask, jsonify
from flask_cors import CORS

#SETUP
app = Flask(__name__)
CORS(app)

#FUNCTIONS
@app.route('/blogs')
def get_blogs():
    blogs = [
        {
            "name": "Example Blog Title",
            "description": "A short summary of the blog post.",
            "url": "https://example.com/blog-post",
            "published": "2025-07-15"
        },
        {
            "name": "Another Blog",
            "description": "Second blog post.",
            "url": "https://example.com/another",
            "published": "2025-06-22"
        }
    ]
    return jsonify(blogs)

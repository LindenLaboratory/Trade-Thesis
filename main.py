#IMPORTS
from flask import Flask, jsonify

#SETUP
app = Flask(__name__)

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

#MAINLOOP
if __name__ == '__main__':
    app.run(debug=True)

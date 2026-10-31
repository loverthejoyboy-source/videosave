from flask import Flask, send_from_directory
from security import init_security
from routes import bp

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 4096
init_security(app)
app.register_blueprint(bp)

@app.get("/")
def home():
    return send_from_directory("static", "index.html")

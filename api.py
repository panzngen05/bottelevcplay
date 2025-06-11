from flask import Flask, request, jsonify, render_template, redirect, session, url_for
import asyncio
from player import play_audio, skip, stop, get_queue, get_now_playing, start_bot
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY")
PANEL_PASSWORD = os.getenv("PANEL_PASSWORD")

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        if request.form.get("password") == PANEL_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("panel"))
        return render_template("login.html", error="Password salah.")
    return render_template("login.html")

@app.route("/panel")
def panel():
    if not session.get("logged_in"):
        return redirect(url_for("home"))
    return render_template("index.html")

@app.route("/play", methods=["POST"])
def play():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    query = request.json.get("query")
    if not query:
        return jsonify({"error": "query required"}), 400
    try:
        title = play_audio(query)
        return jsonify({"status": "playing", "query": title})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/skip", methods=["POST"])
def skip_song():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    asyncio.get_event_loop().create_task(skip())
    return jsonify({"status": "skipped"})

@app.route("/stop", methods=["POST"])
def stop_song():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    asyncio.get_event_loop().create_task(stop())
    return jsonify({"status": "stopped"})

@app.route("/queue", methods=["GET"])
def queue():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"queue": get_queue()})

@app.route("/now", methods=["GET"])
def now():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"now_playing": get_now_playing()})

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())
    app.run(host='0.0.0.0', port=5000)

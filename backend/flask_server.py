from flask import Flask, jsonify
from flask_cors import CORS
import subprocess
import threading

app = Flask(__name__)
CORS(app)  # allow all origins (for development)

def run_snake_game():
    subprocess.run(["python", "snake_game.py"])

@app.route('/start-game', methods=['POST'])
def start_game():
    threading.Thread(target=run_snake_game).start()
    return jsonify({"status": "game started"}), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
 
from flask import Flask, jsonify
import subprocess
import random

app = Flask(__name__)


@app.route('/sleep', methods=['GET'])
def sleep():
    random_number = random.randint(1, 5)
    subprocess.run(["sleep", str(random_number)])
    return jsonify({f"message": f"Slept for {random_number} seconds"})

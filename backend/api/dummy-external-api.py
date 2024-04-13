from flask import Flask, jsonify
import subprocess

@app.route('/sleep', methods=['GET'])
def sleep():
    subprocess.run(["sleep", "10"])
    return jsonify({"message": "Slept for 10 seconds"})
from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route('/query_external_api', methods=['GET'])
def query_external_api():
    response = requests.get('http://localhost:5000/sleep')  # replace with your actual API URL
    data = response.json()
    return jsonify(data)
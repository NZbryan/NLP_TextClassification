# coding:utf-8
from flask import Flask, request, redirect, url_for, flash, jsonify
import json
from predict import CnnModel

app = Flask(__name__)
# app.secret_key = "xxx"

@app.route('/TextClassification/', methods=['POST'])
def makecalc():
    data = request.get_json()
    prediction = model.predict(data)
    return jsonify(prediction)

if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    model = CnnModel()
    app.run(debug=True, host='0.0.0.0')


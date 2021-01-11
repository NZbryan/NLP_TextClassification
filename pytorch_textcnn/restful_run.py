from flask import Flask,request, jsonify
from vali import validsign,_get_request_params
from predict import CnnModel


app = Flask(__name__)

@app.route('/textclf',methods=['POST'])
@validsign(require_token=False, require_sign=True)
def TextCNN():
    params = _get_request_params()
    input_text = params['text']
    cnn_model = CnnModel()
    return jsonify(cnn_model.predict(test_demo))

@app.route('/wu_shouquan',methods=['POST'])
def wu_shouquan():
    return 'easy! wu shou quan'
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

from sanic import Sanic, log
import json
from sanic.response import json as json2
from predict_no_iter import electraModel

app = Sanic()

app = Sanic("my_electra_server")
app.cache_electra = None

async def electra_cls(app):
    app.cache_electra = electraModel()

@app.route('/transformerselectra',methods=['POST'])
async def run_bertModel(request):
#     if globals()['finish_load_model']:
#         pass
#     else:
#         globals()['finish_load_model'] = True
#         globals()['electramodel'] = electraModel()
    args = request.json
    log.logger.info('post data:\n {}'.format(json.dumps(args, indent=4, ensure_ascii=False)))
    input_text = args.get('text')
    return json2(app.cache_electra.predict(input_text))

if __name__ == '__main__':
#     bertmodel = bertModel()
#     app.run(debug=True, host='0.0.0.0',port=8870)
    app.add_task(electra_cls(app))
    app.run(debug=False, host='0.0.0.0', port=8200, workers=2)
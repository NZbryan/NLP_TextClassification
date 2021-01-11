import hashlib
import configparser
from flask import request, jsonify
from flask_restful import reqparse
# from models.user import UserModel
import os

config = configparser.ConfigParser()
path = os.path.abspath(os.path.dirname(__file__)) + "/config.ini"
config.read(path)

# parser = reqparse.RequestParser()
# parser.add_argument('appkey', type=str,required=True)
# parser.add_argument('timestamp', type=str,required=True)
# parser.add_argument('nonce', type=int,required=True)
# parser.add_argument('sign', type=str,required=True)


@staticmethod
def check_token(uid, token):
    if not token or not uid:
        return False
#     user = UserModel.find_user_by_id
    user = "test"
    if not user:
        return False
    if not user.user_auth:
        return False

def signature(params: dict):
    """
    根据请求进行签名
    :param params: 请求参数
    :return:
    """
    commons = ['timestamp', 'nonce', 'appkey', 'sign', 'token']
    m = hashlib.md5()
#     lst = [f"{k}={v}" for k, v in params.items() if k not in commons]
#     lst.sort()
#     msg = '&'.join(lst)
    token = params.get('token', '')
    timestamp = params.get('timestamp', '')
    nonce = params.get('nonce')
    appkey = params.get('appkey', '')
    appsecret = _get_app_secret(appkey)
    m.update(f'{appkey}{timestamp}{nonce}{appsecret}'.encode('utf-8'))
    return m.hexdigest()


def _get_app_secret(appkey: str):
    key = config['APP']['appkey']
    if appkey == key:
        return config['APP']['appsecret']
    return ''


def validsign(require_token=False, require_sign=True):
    """
    验证签名,token信息
    :param require_token: 是否验证token
    :param require_sign: 是否验证签名
    :return:
    """

    def decorator(func):

        def wrapper():

            params = _get_request_params()
            
            if require_sign:
                appkey = params.get('appkey')
                sign = params.get('sign')
                csign = signature(params)
                if not appkey:
                    return make_response_error(300, 'appkey is none.')
                if csign != sign:
                    return make_response_error(500, 'signature is error.')
            if require_token:
                token = params.get('token')
                uid = params.get('userId')
                if not check_token(uid, token):
                    return make_response_error(504, 'no operation permission')
            return func()

        return wrapper

    return decorator


def _get_request_params():
    params = request.form
    if not params:
        params = request.args
    return params


def make_response_error(code, msg):
    """
    请求失败返回的结果
    :param code:
    :param msg:
    :return:
    """
    resp = {'code': code, 'msg': msg}
    return jsonify(resp)

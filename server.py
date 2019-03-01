import json

from flask import Flask, request

from interpreter import *;

app = Flask(__name__)


interpreter_dict = {
    'java': JavaInterpreter(),
    'python': CPlusPlusInterpreter(),
    'gcc': CPlusPlusInterpreter(),
    'g++': CPlusPlusInterpreter(),
    'go': GoInterpreter(),
}


@app.route('/<string:language>/', methods=['POST'])
def execute(language):
    data = json.loads(request.get_json())
    interpreter = interpreter_dict.get(language)
    status, result = interpreter(**data)
    res = {
        'status': status,
        'result': result
    }
    return json.dumps(res)



if __name__ == '__main__':
    app.run()

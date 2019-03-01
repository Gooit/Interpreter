import json

from flask import Flask, request

from interpreter import *

app = Flask(__name__)


interpreter_dict = {
    'java': JavaInterpreter(),
    'python': PythonInterpreter(),
    'gcc': CPlusPlusInterpreter(),
    'g++': CPlusPlusInterpreter(),
    'go': GoInterpreter(),
}


@app.route('/<string:language>/', methods=['POST'])
def execute(language):
    data = request.get_json()
    interpreter = interpreter_dict.get(language)
    response = interpreter(**data)
    return json.dumps(response)



if __name__ == '__main__':
    app.run(host='0.0.0.0')

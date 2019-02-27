from flask import Flask

app = Flask(__name__)


@app.route('/c++/')
def cplusplus():
    return 'Hello World!'


@app.route('/python/')
def python():
    return 'sdf'


@app.route('/java/')
def java():
    return


if __name__ == '__main__':
    app.run()

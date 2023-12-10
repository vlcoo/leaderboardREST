from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hola! rest api roguelike'


if __name__ == '__main__':
    app.run()

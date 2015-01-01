# encoding: utf-8

from bottle import Bottle, static_file, TEMPLATE_PATH
from ueditor import UEditor

TEMPLATE_PATH.append('./templates/')

app = Bottle()
editor = UEditor(app)


@app.route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='./static')


if __name__ == '__main__':
    app.run(host='localhost', port=8080)

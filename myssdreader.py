#!/usr/bin/env python3

"""
MySSD Reader

读取MySSD Daemon记录的数据

myxxxsquared https://github.com/myxxxsquared/myssd-python
"""

import sqlite3
from configparser import ConfigParser
from flask import Flask, send_from_directory, request, render_template, Response

app = Flask(__name__) # pylint: disable=C0103

@app.route("/", methods=['GET'])
def index():
    ''' 网站主页 '''
    return send_from_directory('static', 'index.html')

@app.route("/data", methods=['GET'])
def data():
    ''' 网站信息获取 '''
    return Response(app.get_data(request.args['datafrom']), mimetype='application/json')


@app.route('/shutdown', methods=['POST'])
def shutdown():
    """ 关闭服务器 """
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return ""

class MySSDReader():
    ''' MySSD 读取信息 '''

    def __init__(self):
        config = ConfigParser()
        config.read('myssd.config')
        self.logdb = config.get('logs', 'dbfile')
        self.life = int(config.get('reader', 'life'))
        self.port = int(config.get('reader', 'port'))

        self._switch_list = {
            'current' : self._get_current,
            'hour' : self._get_hour,
            'day' : self._get_day,
            'month' : self._get_month,
            'year' : self._get_year,
            'all' : self._get_all
        }

    def get_data(self, datafrom):
        ''' 从数据库读取数据 '''
        return self._switch_list[datafrom]()

    def _get_current(self):
        ''' 读取当前写入量数据 '''
        with sqlite3.connect(self.logdb) as dbconnect:
            cursor = dbconnect.execute( \
                "SELECT `written` FROM `ssdlog` ORDER BY `written` DESC LIMIT 1;" \
            )
            written = next(cursor)[0]
        written = written / 2097152. / self.life * 100
        return render_template('current.json', written=written)

    def _get_hour(self):
        ''' 读取一个小时内的数据 '''
        return self._get_after('datetime("now", "-1 hour")')

    def _get_day(self):
        ''' 读取一天内的数据 '''
        return self._get_after('datetime("now", "-1 day")')

    def _get_month(self):
        ''' 读取一个月内的数据 '''
        return self._get_after('datetime("now", "-1 month")')

    def _get_year(self):
        ''' 读取一年内的数据 '''
        return self._get_after('datetime("now", "-1 year")')

    def _get_all(self):
        ''' 读取全部数据 '''
        return self._get_after()

    def _get_after(self, time=None):
        ''' 获取某指定时间之后的写入量信息 '''
        time = time or '"1970-01-01 00:00:00"'
        with sqlite3.connect(self.logdb) as dbconnect:
            cursor = dbconnect.execute( \
                "SELECT * FROM `ssdlog` WHERE `time` > {};".format(time) \
            )
            dat = map( \
                lambda x: '{{"x":"{}", "y":{}}}'.format(x[0], x[1]/2097152.), \
                cursor \
            )
            dat = ','.join(dat)
        return render_template('chart.json', data=dat)

def main():
    ''' main 函数 '''
    reader = MySSDReader()
    app.get_data = reader.get_data
    app.run(port=reader.port)

if __name__ == '__main__':
    main()

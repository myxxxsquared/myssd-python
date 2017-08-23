#/usr/bin/env python3

"""
MySSD Deamon
用于在后台运行以检测固态硬盘写入量

myxxxsquared https://github.com/myxxxsquared/myssd-python
"""

from configparser import ConfigParser
import sqlite3
import subprocess
import re
import time

RE_WRITTEN = "0x01\\s+0x018\\s+6\\s+(\\d+)\\s+---\\s+Logical Sectors Written"

SQL_INIT_STRING = '''
    CREATE TABLE IF NOT EXISTS ssdlog(
        time DATETIME,
        written INTEGER
    );
    CREATE TABLE IF NOT EXISTS errorlog(
        time DATETIME,
        info TEXT
    );
'''
SQL_INSERT_SSD = 'INSERT INTO ssdlog (time, written) VALUES (datetime("now"), ?)'
SQL_INSERT_ERR = 'INSERT INTO errorlog (time, info) VALUES (datetime("now"), ?)'

class MySSD:
    """ 检测固态硬盘的写入量 """

    def __init__(self):
        config = ConfigParser()
        config.read('myssd.config')

        self.timeout = config.get('daemon', 'timeout')
        self.span = int(config.get('daemon', 'span'))
        self.logdb = config.get('logs', 'dbfile')

        with sqlite3.connect(self.logdb) as dbconnect:
            dbconnect.executescript(SQL_INIT_STRING)
            dbconnect.commit()

        smartctl = config.get('smartctl', 'bin')
        smartargs = config.get('smartctl', 'args')
        self.commandline = '{} {}'.format(smartctl, smartargs)

        self.rewritten = re.compile(RE_WRITTEN)

    def run(self):
        """ 运行一次写入量记录 """

        process = subprocess.Popen(self.commandline, stdout=subprocess.PIPE)
        try:
            outputs = process.stdout.readlines()
            process.wait(self.timeout)
            if process.returncode:
                raise Exception('smatrctl returned {}'.format(process.returncode))

            match = None
            for line in outputs:
                match = self.rewritten.match(line.decode())
                if match:
                    with sqlite3.connect(self.logdb) as dbconnect:
                        dbconnect.execute(SQL_INSERT_SSD, (match.group(1),))
                        dbconnect.commit()
                    break
            if not match:
                raise Exception('cannot match information in smartctl')

        except Exception as ex:
            with sqlite3.connect(self.logdb) as dbconnect:
                dbconnect.execute(SQL_INSERT_ERR, (str(ex),))
                dbconnect.commit()


def main():
    """ main 函数 """

    myssd = MySSD()
    while True:
        myssd.run()
        time.sleep(myssd.span)

if __name__ == '__main__':
    main()

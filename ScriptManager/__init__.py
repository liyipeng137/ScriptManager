# -*- coding: utf-8 -*-
"""
    :Author: LiYiPeng
"""

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy


#程序名
app = Flask('ScriptManager')
#指定配置文件
app.config.from_pyfile('settings.py')
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
moment = Moment(app)


from ScriptManager import views, errors


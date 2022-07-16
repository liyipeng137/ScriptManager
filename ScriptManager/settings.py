# -*- coding: utf-8 -*-
"""
    :Author: LiYiPeng
"""
import os
import sys
from os import path 
from ScriptManager import app

#SQLite URI compatible
WIN = sys.platform.startswith('win')
if WIN:
   prefix = 'sqlite:///'
else:
   prefix = 'sqlite:////'
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

SECRET_KEY = os.getenv('SECRET_KEY', 'secret string')
SQLALCHEMY_TRACK_MODIFICATIONS = False

#数据库sqllite
# SQLALCHEMY_DATABASE_URI = prefix + os.path.join(basedir, 'data.db')

#数据库mysql
SQLALCHEMY_ENGINE_OPTIONS = {'pool_size': 20, 'pool_recycle': 50, 'pool_pre_ping': True}
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Lyplyp666!@192.168.176.131:3306/ScriptManager'#数据库地址

#文件上传本地路径
UPLOAD_FOLDER = path.join(os.path.abspath('.'),'ScriptManager','script')
#UPLOAD_FOLDER = r'C:\Users\lyp\Desktop\Flask\sayhello\ScriptManager\script'
#脚本上传至服务器的目录
REMOTE_DIR = '/opt' 
#允许上传文件的格式,仅支持shell和python
ALLOWED_EXTENSIONS = set(['sh','py']) 

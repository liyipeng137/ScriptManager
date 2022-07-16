# -*- coding: utf-8 -*-
"""
    :Author: LiYiPeng
"""
from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,String
import time
from werkzeug.security import generate_password_hash, check_password_hash
from ScriptManager import db

class Node(db.Model):
    __tablename__ = 'node'
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(20), unique=True)
    user = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    password = db.Column(db.String(128), nullable=False)
    # 设置访问密码的方法,并用装饰器@property设置为属性,调用时不用加括号
    # @property
    # def password(self):
    #     return self._password
	
    # # 设置加密的方法,传入密码,对类属性进行操作
    # @password.setter
    # def password(self, value):
    #     self._password = generate_password_hash(value)
	
    # # 设置验证密码的方法
    # def check_password(self, user_pwd):
    #     return check_password_hash(self._password, user_pwd)


class Script(db.Model):
    __tablename__ = 'script'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    script_id = db.Column(db.Integer)
    run_type = db.Column(db.Enum('Backup','Crontab'), nullable=False)
    crontabset = db.Column(db.String(12), server_default='')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class Task_Nodes(db.Model):
    __tablename__ = 'task_nodes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    node_id = db.Column(db.Integer, db.ForeignKey('node.id'), nullable=False)
    state = db.Column(db.Enum('stop','start','failed'), server_default='stop', nullable=False)







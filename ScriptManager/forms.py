# -*- coding: utf-8 -*-
"""
    :Author: LiYiPeng
"""

from flask_wtf import FlaskForm
from wtforms import HiddenField,StringField, SubmitField, TextAreaField, SelectField, SelectMultipleField, PasswordField
from wtforms.validators import DataRequired, Length
from ScriptManager.models import *

class HelloForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(1, 20)])
    body = TextAreaField('Message', validators=[DataRequired(), Length(1, 200)])
    submit = SubmitField()

class Addnode(FlaskForm):
    ip = StringField('ip', validators=[DataRequired(), Length(1, 20)])
    user = StringField('user', validators=[DataRequired(), Length(1, 20)])
    password = PasswordField('password', validators=[DataRequired(), Length(1, 128)])
    submit = SubmitField()

class Addtask(FlaskForm):
    taskname = StringField('Taskname', validators=[DataRequired(), Length(1, 20)])
    bindnode = SelectMultipleField('运行节点')
    #bindnode = SelectField('运行节点')
    script = SelectField('脚本文件')
    runtype = SelectField('运行方式')
    crontabset = StringField('Crontab周期(请按 分/时/日/月/周 格式输入:如 * * * * *)',  validators=[Length(1, 20)])
    submit = SubmitField()

    def __init__(self, *args, **kwargs):
        super(Addtask, self).__init__(*args, **kwargs)
        self.bindnode.choices = [(node.id, node.ip)
            for node in Node.query.order_by(Node.timestamp).all()]
        self.script.choices = [(file.id, file.name)
            for file in Script.query.order_by(Script.timestamp).all()]
        self.runtype.choices = [(1,'Backup'),(2,'Crontab')]
    #node.choices = [ (node.id,node.ip) for node in node_list]









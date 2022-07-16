# -*- coding: utf-8 -*-
"""
    :Author: LiYiPeng
"""

from unicodedata import name
from flask import flash, redirect, url_for, render_template, request, send_from_directory, Flask
from werkzeug.utils import secure_filename
from ScriptManager import app, db
from ScriptManager.forms import *
from ScriptManager.models import *
from ScriptManager.mydef import *
import sqlalchemy
import os
from os import path 
import base64

#创建表
db.create_all()

@app.route('/',methods=['GET'])
def index():
    return render_template('index.html')

#增加node
@app.route('/node_manager', methods=['GET', 'POST'])
def node_manager():
    form = Addnode()
    if form.validate_on_submit():
        ip = form.ip.data
        user = form.user.data
        password = form.password.data
        if ssh_check(ip=ip,user=user,password=password) != 'success':
            flash('连接失败!')
        else:
            password_byte = password.encode('utf-8')
            pass_base_data = base64.b64encode(password_byte)  # 加密
            pass_data_str = pass_base_data .decode('utf-8') # 转换为字符串
            node = Node(ip=ip,user=user,password=pass_data_str)
            try:
                db.session.add(node)
                db.session.commit()
            except sqlalchemy.exc.IntegrityError as e:
                db.session.rollback()
                e_str = "".join(e.args[0])
                if e_str.startswith('(pymysql.err.IntegrityError)'):
                    flash("节点已存在")
                else:
                    flash(e_str)
            else:
                flash("连接成功!")
            return redirect(url_for('node_manager'))
    nodes = Node.query.order_by(Node.timestamp.desc()).all()
    return render_template('node_manager.html',form=form,nodes=nodes)

#删除node
@app.route('/delete/<int:node_id>', methods=['POST'])
def delete_node(node_id):
    node = Node.query.get(node_id)
    try:
        db.session.delete(node)
        db.session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        db.session.rollback()
        e_str = "".join(e.args[0])
        flash(e_str)
    else:
        flash("delete node success")
    return redirect(url_for('node_manager'))

#删除文件
@app.route('/delete/file:<filename>', methods=['POST'])
def delete_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'],filename)
    if os.path.isfile(file_path):
        os.remove(file_path)
        db.session.query(Script).filter(Script.name==filename).delete()
        db.session.commit()
        flash("delete  file  success")
        return redirect(url_for('script_manager'))
    else:
        flash("no such file")

#删除任务
@app.route('/delete/task:<task_id>', methods=['POST'])
def delete_task(task_id):
    Task_Nodes.query.filter(Task_Nodes.task_id==task_id).delete()
    Task.query.filter(Task.id==task_id).delete()
    db.session.commit()
    flash("delete task success")
    return redirect(url_for('task_manager'))

#文件管理
@app.route('/script_manager', methods=['GET','POST'])
def script_manager():
    if request.method == 'POST':
        #将上传的文件赋予file
        file = request.files['file'] 
        #当确认有上传文件并且格式合法
        if file and allowed_file(file.filename):
            #使用secure_filename()让文件名变得安全
            filename = secure_filename(file.filename)
            upload_path = path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)
            file = Script(name=filename)
            try:
                db.session.add(file)
                db.session.commit()
            except sqlalchemy.exc.IntegrityError as e:
                db.session.rollback()
                e_str = "".join(e.args[0])
                if e_str.startswith('(pymysql.err.IntegrityError)'):
                    flash("文件已存在")
                else:
                    flash(e_str)
            else:
                flash("Add file success!")
            return redirect(url_for('script_manager'))
        else:
            flash("文件为空或检查文件格式")
            return redirect(url_for('script_manager'))
    if request.method == 'GET':
        file_dir = app.config['UPLOAD_FOLDER']
        files = os.listdir(file_dir)
        return render_template('script_manager.html',files=files)

#任务管理
@app.route('/task_manager', methods=['GET','POST'])
def task_manager():
    form = Addtask()
    if request.method == 'POST':
        taskname = request.form.get('taskname')
        script_id = request.form.get('script')
        bindnode_id = request.form.getlist('bindnode')
        run_type = request.form.get('runtype')
        crontabset = request.form.get('crontabset')
        #校验Crontab格式
        if crontabset != '':
            if  cron_check(crontabset): 
                #addtask
                task = Task(name=taskname,script_id=script_id,run_type=run_type,crontabset=crontabset)
            else:
                flash("请检查Crontab格式!")
                return redirect(url_for('task_manager'))
        else:
            task = Task(name=taskname,script_id=script_id,run_type=run_type)    
        try:
            #先写入Task表
            db.session.add(task)
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            db.session.rollback()
            e_str = "".join(e.args[0])
            flash(e_str)
            return redirect(url_for('task_manager'))
        else:
            #写入中间表
            task_id = Task.query.filter(Task.name == taskname).one().id
            for i in bindnode_id:
                task_node = Task_Nodes(task_id=task_id,node_id=i)
                try:
                    db.session.add(task_node)
                    db.session.commit()
                except sqlalchemy.exc.IntegrityError as e:
                    db.session.rollback()
                    e_str = "".join(e.args[0])
                    flash(e_str)
                    return redirect(url_for('task_manager'))
            flash("Add task success!")
        return redirect(url_for('task_manager'))

    elif request.method == 'GET':
        tasks = Task.query.order_by(Task.timestamp.desc()).all()
        scripts = Script.query.all()
        nodes = Node.query.all()
        return render_template('task_manager.html',form=form,tasks=tasks,nodes=nodes,scripts=scripts,task_show=Task_show)

#刷新任务状态
@app.route('/flush_staskstate',methods=['POST'])
def flush_taskstate():
    log.info("刷新任务状态")
    tasks = Task.query.order_by(Task.timestamp.desc()).all()
    #检查任务状态
    for task in tasks:
        task_id = task.id
        task_node_running,task_node_unrunning = check_task_def(task_id)
        nodes_all = Task_Nodes.query.filter(Task_Nodes.task_id == task_id).with_entities(Task_Nodes.node_id).all()
        for i in nodes_all:
            node_id = i[0]
            task=Task_c(task_id,node_id)
            task_state_old = task.state()
            if node_id in task_node_unrunning and task_state_old == 'start':
                log.info("更新状态start-->stop:",node_id)
                Task_Nodes.query.filter(and_(Task_Nodes.task_id == task_id,Task_Nodes.node_id == node_id)).update({Task_Nodes.state:'stop'}) 
                db.session.commit()
            elif node_id in task_node_running and task_state_old != 'start':
                log.info("更新状态unstart-->start:",node_id)
                Task_Nodes.query.filter(and_(Task_Nodes.task_id == task_id,Task_Nodes.node_id == node_id)).update({Task_Nodes.state:'start'}) 
                db.session.commit()
    return redirect(url_for('task_manager'))

@app.route('/start_task/task:<task_id>',methods=['POST'])
def start_task(task_id):
    success_con,failed_con = start_task_def(task_id)
    flash_message = str(("Success:%s  Failed:%s" %(success_con,failed_con)))
    flash(flash_message)
    return redirect(url_for('task_manager'))

@app.route('/stop_task/task:<task_id>',methods=['POST'])
def stop_task(task_id):
    stop_task_def(task_id)
    return redirect(url_for('task_manager'))






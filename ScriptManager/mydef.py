# -*- coding: utf-8 -*-
"""
    :Author: LiYiPeng
"""
from operator import and_
import paramiko
import os
import re
import sqlalchemy
from ScriptManager.models import *
from os import path 
from ScriptManager import app
from scp import SCPClient
import base64

import logging
from logging import handlers
 
 
# 日志输出
class Logger(object):
    # 日志级别关系映射
    level_relations = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }
    def __init__(self, filename="scriptmanager.log", level="info", when="D", backupCount=3, fmt="%(asctime)s - %(filename)s[line:%(lineno)d] - %"                                                                                      "(levelname)s: %(message)s"):
        # 设置日志输出格式
        format_str = logging.Formatter(fmt)
        # 设置日志在控制台输出
        streamHandler = logging.StreamHandler()
        # 设置控制台中输出日志格式
        streamHandler.setFormatter(format_str)
        # 设置日志输出到文件（指定间隔时间自动生成文件的处理器  --按日生成）
        # filename：日志文件名，interval：时间间隔，when：间隔的时间单位， backupCount：备份文件个数，若超过这个数就会自动删除
        fileHandler = handlers.TimedRotatingFileHandler(filename=filename, when=when, backupCount=backupCount, encoding="utf-8")
        # 设置日志文件中的输出格式
        fileHandler.setFormatter(format_str)
        # 设置日志输出文件
        self.logger = logging.getLogger(filename)
        # 设置日志级别
        self.logger.setLevel(self.level_relations.get(level))
        # 将输出对象添加到logger中
        self.logger.addHandler(streamHandler)
        self.logger.addHandler(fileHandler)
log = Logger(level="info").logger

class Task_c(object):
    def __init__(self,task_id,node_id=0):
        self.task_id = task_id 
        self.node_id = node_id
    def node_ip(self):
        bindnode_ip = Node.query.get(self.node_id).ip
        return(bindnode_ip)
    def node_user(self):
        bindnode_user = Node.query.get(self.node_id).user
        return(bindnode_user)
    def node_password(self):
        bindnode_password = Node.query.get(self.node_id).password
        #解密
        pass_byte = base64.b64decode(bindnode_password)
        pass_str  = pass_byte.decode('utf-8')
        return(pass_str)
    def state(self):
        state = Task_Nodes.query.filter(and_(Task_Nodes.task_id == self.task_id,Task_Nodes.node_id == self.node_id)).first().state
        return(state)
    def script_name(self):
        script_id = Task.query.get(self.task_id).script_id
        script_name = Script.query.get(script_id).name
        return(script_name)
    def runtype(self):
        runtype = Task.query.get(self.task_id).run_type
        return(runtype)
    def crontabset(self):
        crontabset = Task.query.get(self.task_id).crontabset
        return(crontabset)
    def name(self):
        name = Task.query.get(self.task_id).name
        return(name)

class Task_show(object):
    def __init__(self,task_id):
        self.task_id = task_id 
    def get_node_list(self):
        node_list=[]
        nodes_all = Task_Nodes.query.filter(Task_Nodes.task_id == self.task_id).with_entities(Task_Nodes.node_id).all()
        for i in nodes_all:
            node_id = i[0]
            node_ip = Node.query.get(node_id).ip
            node_list.append(node_ip)
        return(node_list)
    def get_task_state(self):
        task_node_start = []
        task_node_stop = []
        task_node_failed = []
        nodes_all = Task_Nodes.query.filter(Task_Nodes.task_id == self.task_id).with_entities(Task_Nodes.node_id).all()
        for i in nodes_all:
            node_id = i[0]
            node_ip = Node.query.get(node_id).ip
            task_node = Task_Nodes.query.filter(and_(Task_Nodes.task_id == self.task_id,Task_Nodes.node_id == node_id)).with_entities(Task_Nodes.state).all()
            if task_node[0][0] == 'start':
                task_node_start.append(node_ip)
            elif task_node[0][0] == 'stop':
                task_node_stop.append(node_ip)
            elif task_node[0][0] == 'failed':
                task_node_failed.append(node_ip)
        return(task_node_start,task_node_stop,task_node_failed)

#验证ssh连接是否成功
def ssh_check(ip,user,password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
    # 建立连接
        ssh.connect(ip, username=user, port=22, password=password)
    except:
        return("failed")
    else:
        return("success") 

#验证crontab格式是否正确
def cron_check(crontabset):
    re_cron = '(((\d+,)+\d+|(\d+(\/|-)\d+)|\d+|\*|\*\/\d) ?){5,7}'
    result = re.search(re_cron,crontabset)
    if result:
        return True
    else:
        return False

#验证文件格式是否在允许上传格式范围之内
def allowed_file(filename):
    allowed_extensions = app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1] in allowed_extensions

#任务启动
def start_task_def(task_id):
    #远程上传路径
    remote_path = app.config['REMOTE_DIR']
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #关联的所有节点ID
    nodes_all = Task_Nodes.query.filter(Task_Nodes.task_id == task_id).with_entities(Task_Nodes.node_id).all()
    #启动任务
    log.info("Start task...: %s" %task_id)
    for  i in nodes_all:
        node_id = i[0]
        task=Task_c(task_id,node_id)
        #本地脚本位置
        file_path = path.join(app.config['UPLOAD_FOLDER'], task.script_name())
        try:
            #建立连接
            ssh.connect(task.node_ip(), username=task.node_user(), port=22, password=task.node_password())
        except:
            #连不上就跳过
            log.error("%s: ssh连接失败" %task.node_ip())
            continue
        else:
            #上传脚本文件
            log.info("上传%s至服务器..." %task.script_name())
            scpclient = SCPClient(ssh.get_transport(),socket_timeout=15.0)
            scpclient.put(file_path, remote_path)
            #shell脚本
            if task.script_name().endswith('.sh'): 
                #语法检查
                ss_check = ("sh -n /opt/" + task.script_name())
                stdin, stdout, stderr = ssh.exec_command(ss_check)
                check_result = stderr.read().decode().replace('/n','').replace(' ','')
                if len(check_result) == 0:
                    log.info("shell语法检查通过")
                    #判断执行类型
                    if task.runtype() == 'Backup':
                        #后台执行脚本文件
                        ssh_command = ("nohup sh /opt/" + task.script_name() + " 2>&1 >/dev/null &")
                        log.info("执行命令: %s" %ssh_command)
                        ssh.exec_command(ssh_command)
                        ssh.close()
                    elif task.runtype() == 'Crontab':
                        #增加定时任务执行
                        ssh_command = ('crontab -l > crontab_tmp && echo "#Script-Manager:' + task.name() + '" >> crontab_tmp &&  echo "' + task.crontabset() + ' /bin/sh /opt/' + task.script_name() + ' 2>&1 >>/opt/' + task.script_name().split('.sh')[0] + '.log" >> crontab_tmp && crontab crontab_tmp && rm -f crontab_tmp')
                        log.info("执行命令: %s" %ssh_command)
                        ssh.exec_command(ssh_command)
                        ssh.close()
                else:
                    log.warning("%s: 语法检查不通过, %s" %(task.script_name(),check_result))
            #python脚本
            elif task.script_name().endswith('.py'):
                #语法检查
                file_path = path.join(app.config['UPLOAD_FOLDER'], task.script_name())
                py_check = ("pyflakes.exe " + file_path)
                check_result = os.popen(py_check).read()
                if len(check_result) == 0:
                    log.info("python语法检查通过")
                    if task.runtype == 'Backup':   
                        #执行脚本文件
                        ssh_command = ("nohup python3 /opt/" + task.script_name() + " 2>&1 >/dev/null &")
                        log.info("执行命令: %s" %ssh_command)
                        ssh.exec_command(ssh_command)
                        ssh.close()
                    else:
                        #增加定时任务执行
                        ssh_command = ('crontab -l > crontab_tmp && echo "#Script-Manager:' + task.name() + '" >> crontab_tmp &&  echo "' + task.crontabset() + ' . /etc/profile;python3 /opt/' + task.script_name() + ' 2>&1 >>/opt/' + task.script_name().split('.sh')[0] + '.log" >> crontab_tmp && crontab crontab_tmp && rm -f crontab_tmp')
                        ssh.exec_command(ssh_command)
                        log.info("执行命令: %s" %ssh_command)
                        ssh.close()
                else:
                    log.warning("%s: 语法检查不通过, %s" %(task.script_name(),check_result))

    #启动任务后检查执行情况
    task_node_running,task_node_unrunning = check_task_def(task_id)
    for id in task_node_running:
        Task_Nodes.query.filter(and_(Task_Nodes.task_id == task_id,Task_Nodes.node_id == id)).update({Task_Nodes.state:'start'})
        db.session.commit()
    for id in task_node_unrunning:
        Task_Nodes.query.filter(and_(Task_Nodes.task_id == task_id,Task_Nodes.node_id == id)).update({Task_Nodes.state:'failed'}) 
        db.session.commit()
    return (len(task_node_running),len(task_node_unrunning))
        

#检查任务执行情况(传入任务ID)
def check_task_def(task_id):
    task_node_running = []
    task_node_unrunning = []
    task_runtype = Task.query.get(task_id).run_type
    #获取该任务关联的所有node_id
    nodes_all = Task_Nodes.query.filter(Task_Nodes.task_id == task_id).with_entities(Task_Nodes.node_id).all()
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    log.info("检查任务状态: %s" %task_id)
    for i in nodes_all:
        node_id = i[0]
        task=Task_c(task_id,node_id)
        if task_runtype == 'Backup':
            ssh_command_check = ("ps -ef | grep " + task.script_name() + "| grep -v grep")
        else:
            ssh_command_check = ("crontab -l | grep " + task.name() + "| grep -v grep")
        try:
            ssh.connect(task.node_ip(), username=task.node_user(), port=22, password=task.node_password())
        except:
            log.error("%s: ssh连接失败" %task.node_ip())
            continue
        else:
            stdin, stdout, stderr = ssh.exec_command(ssh_command_check)
            check_line = stdout.readline()
            ssh.close()
            if check_line == '':
                #未运行
                log.info("任务: %s ,节点: %s  未运行" %(task.name(),task.node_ip()))
                task_node_unrunning.append(node_id)
            else:
                #运行中
                log.info("任务: %s ,节点: %s  运行中" %(task.name(),task.node_ip()))
                task_node_running.append(node_id)
    #返回运行成功和不成功的Node列表
    return(task_node_running,task_node_unrunning)

#停止任务
def stop_task_def(task_id):
    ssh_stop = paramiko.SSHClient()
    ssh_stop.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    task_runtype = Task.query.get(task_id).run_type
    #关联该任务的所有节点ID
    nodes_all = Task_Nodes.query.filter(Task_Nodes.task_id == task_id).with_entities(Task_Nodes.node_id).all()
    log.info("停止任务: %s" %task_id)
    for  i in nodes_all:
        node_id = i[0]
        task=Task_c(task_id,node_id)
        if task_runtype == 'Backup':
            ssh_stop_command = ("kill -9 `ps -ef | grep " + task.script_name() + "| grep -v grep |awk -F' ' '{print $2}'`")
        else:
            ssh_stop_command = ('crontab -l > crontab_tmp && sed -i "/#Script-Manager:' + task.name() + '/,+1d" crontab_tmp && crontab crontab_tmp && rm -f crontab_tmp')
        try:
            #建立连接
            ssh_stop.connect(task.node_ip(), username=task.node_user(), port=22, password=task.node_password())
        except:
            #连不上就跳过
            log.error("%s: ssh连接失败" %task.node_ip())
            continue
        else:
            stdin, stdout, stderr = ssh_stop.exec_command(ssh_stop_command)
            ssh_stop.close()
    #Stop后检查是否成功
    task_node_running,task_node_unrunning = check_task_def(task_id)
    for node_id in task_node_unrunning:
        Task_Nodes.query.filter(and_(Task_Nodes.task_id == task_id,Task_Nodes.node_id == node_id)).update({Task_Nodes.state:'stop'}) 
        db.session.commit()
    log.info("Stop Success: %s" %task_id)
    return









    
import os
import time

import paramiko
from time import sleep
from logger import logger


class MubaojinProject:

    def __init__(self):
        self.transport = paramiko.Transport(('8.140.145.98',22))
        self.transport.connect(username='root',password='Simonvic111')
        self.ssh = paramiko.SSHClient()
        self.ssh._transport = self.transport
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        path = (os.path.dirname(__file__) + r'\CI.log')
        self.logger = logger(path=path).get_logger()
        #git存放在本地的路径
        self.project_path = 'E:\woniusales1'
        #github远程仓库的url
        self.project_git_url = 'https://github.com/mubaojin/woniusales.git'
        #war包名称
        self.war_name = 'woniusales.war'
        #本地war包路径
        self.war_file_path = os.path.join(self.project_path,self.war_name)
        #远程webapps_war包路径
        self.remote_weapps_path = '/root/tomcat_webapps/' + self.war_name
        #服务器db.properties路径
        self.dbproperties_path = '/root/tomcat_webapps/woniusales/WEB-INF/classes/db.properties'
        #docker mysql IP及端口
        self.docker_mysql = '172.17.0.2:3306'
        #docker tomcat --name
        self.tomcat_name = 'tomcat-8.0'
        self.sftp.put(r'E:\woniusales1\woniusales.war',r'/root/tomcat_webapps/woniusales.war')


    def git_update_code(self):
        '''
            从git上获取源代码
        :return: None
        '''
        if os.path.exists(self.project_path):
            # 如果存在该文件夹
            x = os.system(f'git -C {self.project_path} pull')
            # 语句执行成功返回值为0，否则为出错
            if x == 0:
                self.logger.debug('git update project success')
            else:
                self.logger.error('git update project error!')
        else:
            # 如果不存在
            x = os.system(f'git clone {self.project_git_url} {self.project_path}')
            # 语句执行成功返回值为0，否则为出错
            if x == 0:
                self.logger.debug('git clone project success')
            else:
                self.logger.error('git clone project error!')
                raise Exception('git clone project error!')

    def build(self):
        '''
            使用ant构建项目
        :return: None
        '''
        #硬定时
        x = os.system(rf'ant -f {os.path.join(self.project_path,"build.xml")}')
        # 语句执行成功返回值为0，否则为出错
        if x == 0:
            self.logger.debug('project build success')
        else:
            self.logger.error('project build error!')
            raise Exception('project build error!')

    def deploy(self):
        '''
            部署项目到服务器
        :return: None
        '''
        #删除远端war包及部署文件
        #发送war包到服务器,并等待热部署
        try:
            self.ssh.exec_command(f'docker stop {self.tomcat_name}')
            self.logger.debug(f'stop docker {self.tomcat_name}')
            self.ssh.exec_command('rm -rf /root/tomcat_webapps/*')
            self.sftp.put(self.war_file_path,self.remote_weapps_path)
            time.sleep(5)
            self.ssh.exec_command(f'docker start {self.tomcat_name}')
            self.logger.debug(f'start docker {self.tomcat_name}')
            time.sleep(3)
            self.logger.debug('transport war package to server success')
        except Exception as e:
            self.logger.error('transport war package to server error!')
            raise e
        cmd = f'''echo "db_url=jdbc:mysql://{self.docker_mysql}/woniusales?useUnicode=true&characterEncoding=utf8" > {self.dbproperties_path}
        echo "db_username=root" >> {self.dbproperties_path}
        echo "db_password=Simonvic11!" >> {self.dbproperties_path}
        echo "db_driver=com.mysql.jdbc.Driver" >> {self.dbproperties_path}
        '''
        #修改db.properties文件
        res = self.ssh.exec_command(cmd)
        # 重启docker tomcat
        self.ssh.exec_command(rf'docker restart {self.tomcat_name}')
        self.logger.debug('restart tomcat docker')
        sleep(2)






if __name__ == '__main__':
    wp = MubaojinProject()
    wp.git_update_code()
    wp.build()
    wp.deploy()
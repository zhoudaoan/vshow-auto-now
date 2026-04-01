# -*- coding:utf-8 -*-
import os
import smtplib
import email
import zipfile
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import logging

logger = logging


def send_email():
    # 发件人邮箱地址
    username = 'daoan.zhou@v.show'
    # 发件人邮箱密码
    password = ''
    # 自定义的回复地址
    replyto = ''

    From = formataddr(["Auto_Test_html_report", ''])  # 昵称+发信地址(或代发)
    to = ','.join(['', ''])

    cc = ''
    bcc = ''

    # 收件人地址或是地址列表，支持多个收件人
    rcptto = ["18225550463@163.com"]

    # 构造附件对象
    msg = MIMEMultipart('alternative')
    filename = 'vshow_auto_report.zip'
    path = './vshow_auto_report.zip'
    with open(path, 'rb') as f:
        attachment = MIMEApplication(f.read(), _subtype='zip')
    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
    msg.attach(attachment)
    msg['Subject'] = Header('自动化测试报告')
    msg['from'] = From
    msg['To'] = to
    msg['Cc'] = cc
    msg['rcptto'] = ','.join(rcptto)
    logger.info('收件列表：', msg['rcptto'], type(msg['rcptto']))
    msg['Reply-to'] = replyto
    msg['Message-id'] = email.utils.make_msgid()
    msg['Date'] = email.utils.formatdate()

    # 构建alternative的text/plain部分
    textplain = MIMEText('本邮件仅为发送前的最新一次数据,解压后，点击clickme.bat文件，既可以浏览报告。',
                         _subtype='plain', _charset='UTF-8')
    msg.attach(textplain)
    # 构建alternative的text/html部分
    texthtml = MIMEText('自动化运行结果--', _subtype='html', _charset='UTF-8')
    msg.attach(texthtml)

    try:
        client = smtplib.SMTP_SSL('smtp.feishu.cn', 465)
        logger.info('服务和端口连通')
    except:
        logger.error('服务和端口不通')
        exit(1)

    # 开启DEBUG模式
    try:
        client.set_debuglevel(0)
        client.login(username, password)
        logger.info('账密验证成功')
    except:
        logger.error('账密验证失败')
        exit(1)

    client.sendmail(username, msg['rcptto'].split(','), msg.as_string())
    client.quit()
    logger.info('邮件发送成功！')


def zipDir():
    if os.path.exists('vshow_auto_report.zip'):
        try:
            os.remove('vshow_auto_report.zip')
            logger.info("文件 vshow_auto_report.zip 已删除。")
        except OSError as e:
            logger.error(f"删除文件时出错: {e}")
    zip = zipfile.ZipFile(r"vshow_auto_report.zip", "w", zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(r"vshow_auto_report"):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(r"vshow_auto_report", '')

        for filename in filenames:
            zip.write(os.path.join(path, filename), os.path.join(fpath, filename))
    zip.close()
    logger.info('压缩成功')


if __name__ == "__main__":
    zipDir()
    send_email()

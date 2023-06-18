import smtplib
from email.message import EmailMessage 
def sendmail(to,body,subject):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('saginalaazeez21@gmail.com','lfwpdighpzsavkzl')
    msg=EmailMessage()
    msg['From']='saginalaazeez21@.gmail.com'
    msg['Subject']=subject
    msg['To']=to
    msg.set_content(body)
    server.send_message(msg)
    server.quit()
def recievemail(body,subject):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('saginalaazeez21@gmail.com','lfwpdighpzsavkzl')
    msg=EmailMessage()
    msg['From']='saginalaazeez21@gmail.com'
    msg['Subject']=subject
    msg['To']='saginalaazeez21@gmail.com'
    msg.set_content(body)
    server.send_message(msg)
    server.quit()


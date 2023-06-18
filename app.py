from flask import Flask,render_template,url_for,request,session,flash,redirect,abort
from flask_session import Session
from smail import sendmail,recievemail
from keys import secret_key,salt,salt2,salt3
from itsdangerous import URLSafeTimedSerializer
from tokens import token
import
import os
import mysql.connector
app=Flask(__name__)
app.secret_key=secret_key
app.config['SESSION_TYPE']='filesystem'
Session(app)
#mydb=mysql.connector.connect(host='localhost',user='root',password='heez@1183',db='fwr')
db= os.environ['RDS_DB_NAME']
user=os.environ['RDS_USERNAME']
password=os.environ['RDS_PASSWORD']
host=os.environ['RDS_HOSTNAME']
port=os.environ['RDS_PORT']
with mysql.connector.connect(host=host,user=user,password=password,db=db) as conn:
    cursor=conn.cursor(buffered=True)
    cursor.execute('create table if not exists donors(username varchar(15) primary key,password varchar(15),email varchar(50),email_status enum("confirmed","not confirmed"),mblnum bigint(20))')
    cursor.execute('create table if not exists food(fid BINARY(16) primary key,quantity varchar(50),E_date date,items varchar(100),given_by VARCHAR(20),datedate TIMESTAMP DEFAULT CURRENT_TIMESTAMP on update current_timestamp,FOREIGN KEY (given_by) REFERENCES users(username))')
    cursor.execute('create table if not exists benf(username varchar(20) primary key,password varchar(20),Benf_name varchar(20),SWname vachar(20),email varchar(100),email_status enum("confirmed","not confirmed"),mblnum bigint(20))')
mydb=mysql.connector.connect(host=host,user=user,password=password,db=db)
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/registration',methods=['GET','POST'])
def registration():  
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        email=request.form['email']
        mblnum=request.form['mblnum']
        cursor=mydb.cursor(buffered=True)
        try:
            cursor.execute('insert into donors (username,password,email,mblnum) values(%s,%s,%s,%s)',(username,password,email,mblnum))
        except mysql.connector.IntegrityError:
            flash('Username or Email is already Exist')
            return redirect(url_for('registration'))
        else:        
            mydb.commit()
            cursor.close()
            subject='Email Confirmation'
            confirm_link=url_for('confirm',token=token(email),_external=True)
            body=f"Welcome to Food Wastage Reduction, Please Follow this link-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Please confirm link for further process')
            return redirect(url_for('login'))
    return render_template('registration.html')
@app.route('/confirm/<token>')
def confirm(token):  
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        email=serializer.loads(token,salt=salt,max_age=120)
    except:
        abort(404,'Link expired')
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from donors where email=%s',[email])
        status=cursor.fetchone()
        cursor.close()
        if status=='confirmed':
            flash('Email already confirmed')
            return redirect(url_for('login'))
        else:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("update donors set email_status='confirmed' where email=%s",[email])
            mydb.commit()
            flash('Email confirmation success')
            return redirect(url_for('login'))

@app.route('/inactive')
def inactive():  
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from donors where username=%s',[username])
        status=cursor.fetchone()[0]
        cursor.close()
        if status=='confirmed':
            return redirect(url_for('homepage'))
        else:
            return render_template('inactive.html')
    else:
        return redirect(url_for('login'))
@app.route('/login',methods=['GET','POST'])
def login():  
    if session.get('user'):
        return redirect(url_for('homepage'))
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from donors where username=%s',[username])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.execute('select count(*) from donors where username=%s and password=%s',[username,password])
            p_count=cursor.fetchone()[0]
            if p_count==1:
                session['user']=username
                cursor.execute('select email_status from donors where username=%s',[username])
                status=cursor.fetchone()[0]
                cursor.close()
                if status!='confirmed':
                    return redirect(url_for('inactive'))
                else:
                    return redirect(url_for('homepage'))
            else:
                cursor.close()
                flash('invalid password')
                return render_template('login.html')
        else:
            cursor.close()
            flash('invalid username')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
@app.route('/homepage',methods=['GET','POST'])
def homepage():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from donors where username=%s',[username])
        status=cursor.fetchone()[0]
        cursor.close()
        if status=='confirmed':
            if request.method=='POST':
                result=f"%{request.form['search']}%"
                cursor=mydb.cursor(buffered=True)
                cursor.execute("select bin_to_uuid(fid) as uid,quantity,E_date,items from food where quantity like %s and given_by=%s",[result,username])
                data=cursor.fetchall()
                if len(data)==0:
                    data='empty'
                return render_template('donationdata.html',data=data)
            return render_template('homepage.html')
        else:
            return redirect(url_for('inactive'))
    else:
        return redirect(url_for('login'))
@app.route('/resendconfirmation')
def resend():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from donors where username=%s',[username])
        status=cursor.fetchall()
        cursor.execute('select email from donors where username=%s',[username])
        email=cursor.fetchone()[0]
        cursor.close()
        if status=='confirmed':
            flash('Email already confirmed')
            return redirect(url_for('homepage'))
        else:
            subject='Email Confirmation'
            confirm_link=url_for('confirm',token=token(email),salt=salt,_external=True)
            body=f"Please confirm your mail-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Confirmation link sent check your email')
            return redirect(url_for('inactive'))
    else:
        return redirect(url_for('login'))
@app.route('/forget',methods=['GET','POST'])
def forgot():
    if request.method=='POST':
        email=request.form['email']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from  donors where email=%s',[email])
        count=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('SELECT email_status from  donors where email=%s',[email])
            status=cursor.fetchone()[0]
            cursor.close()
            if status!='confirmed':
                flash('Please Confirm your email first')
                return render_template('forgot.html')
            else:
                subject='Forget Password'
                confirm_link=url_for('reset',token=token(email),salt=salt2,_external=True)
                body=f"Use this link to reset your password-\n\n{confirm_link}"
                sendmail(to=email,body=body,subject=subject)
                flash('Reset link sent check your email')
                return redirect(url_for('login'))
        else:
            flash('Invalid email id')
            return render_template('forgot.html')
    return render_template('forgot.html')
@app.route('/reset/<token>',methods=['GET','POST'])
def reset(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        email=serializer.loads(token,salt=salt2,max_age=3600)
    except Exception as e:
        print(e)
        # abort(404,'Link Expired')

    if request.method=='POST':
        email=request.form['email']
        newpassword=request.form['npassword']
        confirmpassword=request.form['cpassword']
        if newpassword==confirmpassword:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update donors set password=%s where email=%s',[newpassword,email])
            mydb.commit()
            flash('Reset Successful')
            return redirect(url_for('login'))
        else:
            flash('Passwords mismatched')
            return render_template('newpassword.html')
    return render_template('newpassword.html')
@app.route('/donate',methods=["GET","POST"])
def donate():
    if session.get('user'):
        if request.method=='POST':
            quantity=request.form['quantity']
            E_date=request.form['date']
            items=request.form['items']
            username=session.get('user')
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into food (fid,quantity,E_date,items,given_by) values(UUID_TO_BIN(UUID()),%s,%s,%s,%s)',[quantity,E_date,items,username])
            mydb.commit()
            cursor.close()
            subject='Alert Food is Available'
            body=f"We got food from {username}, items are {items} lets check and give to needy"
            recievemail(body=body,subject=subject)
            flash('Food details recieved, we will contact you in short time')
            flash('food donated Sucessfully')
            return redirect(url_for('homepage'))
        return render_template('donate.html')
    else:
        return redirect(url_for('login'))

@app.route('/history')
def history():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select bin_to_uuid(fid) as uid,quantity,E_date,items,datedate from food where given_by=%s order by datedate desc',[username])
        data=cursor.fetchall()
        cursor.close()
        return render_template('donationdata.html',data=data)
    else:
        return redirect(url_for('login'))
@app.route('/fid/<uid>')
def fidv(uid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select bin_to_uuid(fid),quantity,E_date,items,datedate from food where bin_to_uuid(fid)=%s',[uid])
        cursor.close()
        uid,quantity,E_date,items,datedate=cursor.fetchone()
        return render_template('history.html',quantity=quantity,E_date=E_date,items=items,date=datedate)
    else:
        return redirect(url_for('login'))


# Beneficiary code-------------------------------------->

@app.route('/rregistration',methods=['GET','POST'])
def rregistration():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        benf_name=request.form['bname']
        swname=request.form['sname']
        email=request.form['email']
        mblnum=request.form['mblnum']
        cursor=mydb.cursor(buffered=True)
        try:
            cursor.execute('insert into benf (username,password,benf_name,SWname,email,mblnum) values(%s,%s,%s,%s,%s,%s)',(username,password,benf_name,swname,email,mblnum))
        except mysql.connector.IntegrityError:
            flash('Username or Email is already Exist')
            return redirect(url_for('rregistration'))
        else:        
            mydb.commit()
            cursor.close()
            subject='Email Confirmation'
            confirm_link=url_for('confirm',token=token(email),_external=True)
            body=f"Welcome to Food Wastage Reduction, Please Follow this link-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Please confirm link for further process')
            return redirect(url_for('rlogin'))
    return render_template('rregistration.html')
@app.route('/rconfirm/<token>')
def rconfirm(token):  
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        email=serializer.loads(token,salt=salt,max_age=120)
    except:
       abort(404,'Link expired')
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from benf where email=%s',[email])
        status=cursor.fetchone()[0]
        cursor.close()
        if status=='confirmed':
            flash('Email already confirmed')
            return redirect(url_for('rlogin'))
        else:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("update benf set email_status='confirmed' where email=%s",[email])
            mydb.commit()
            flash('Email confirmation success')
            return redirect(url_for('rlogin'))
@app.route('/rinactive')
def rinactive():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from benf where username=%s',[username])
        status=cursor.fetchone()[0]
        cursor.close()
        if status=='confirmed':
            return redirect(url_for('rhomepage'))
        else:
            return render_template('rinactive.html')
    else:
        return redirect(url_for('rlogin'))
@app.route('/rlogin',methods=['GET','POST'])
def rlogin():
    if session.get('user'):
        return redirect(url_for('rhomepage'))
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from benf where username=%s',[username])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.execute('select count(*) from benf where username=%s and password=%s',[username,password])
            p_count=cursor.fetchone()[0]
            if p_count==1:
                session['user']=username
                cursor.execute('select email_status from benf where username=%s',[username])
                status=cursor.fetchone()[0]
                cursor.close()
                if status!='confirmed':
                    return redirect(url_for('rinactive'))
                else:
                    return redirect(url_for('rhomepage'))
            else:
                cursor.close()
                flash('invalid password')
                return render_template('rlogin.html')
        else:
            cursor.close()
            flash('invalid username')
            return render_template('rlogin.html')
    return render_template('rlogin.html')
@app.route('/rhomepage',methods=['GET','POST'])
def rhomepage():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from benf where username=%s',[username])
        status=cursor.fetchone()[0]
        cursor.close()
        if status=='confirmed':
            if request.method=='POST':
                result=f"%{request.form['search']}%"
                cursor=mydb.cursor(buffered=True)
                cursor.execute("select bin_to_uuid(fid) as uid,quantity,E_date,items from food where quantity like %s and given_by=%s",[result,username])
                data=cursor.fetchall()
                if len(data)==0:
                    data='empty'
                return render_template('donationdata.html',data=data)
            return render_template('rhomepage.html')
        else:
            return redirect(url_for('rinactive'))
    else:
        return redirect(url_for('rlogin'))
@app.route('/rresendconfirmation')
def rresend():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from benf where username=%s',[username])
        status=cursor.fetchone()[0]
        cursor.execute('select email from benf where username=%s',[username])
        email=cursor.fetchone()[0]
        cursor.close()
        if status=='confirmed':
            flash('Email already confirmed')
            return redirect(url_for('rhomepage'))
        else:
            subject='Email Confirmation'
            confirm_link=url_for('rconfirm',token=token(email),salt=salt3,_external=True)
            body=f"Please confirm your mail-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Confirmation link sent check your email')
            return redirect(url_for('rinactive'))
    else:
        return redirect(url_for('rlogin'))
@app.route('/rforget',methods=['GET','POST'])
def rforgot():
    if request.method=='POST':
        email=request.form['email']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from benf where email=%s',[email])
        count=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('SELECT email_status from benf where email=%s',[email])
            status=cursor.fetchone()[0]
            cursor.close()
            if status!='confirmed':
                flash('Please Confirm your email first')
                return render_template('rforgot.html')
            else:
                subject='Forget Password'
                confirm_link=url_for('rreset',token=token(email),salt=salt2,_external=True)
                body=f"Use this link to reset your password-\n\n{confirm_link}"
                sendmail(to=email,body=body,subject=subject)
                flash('Reset link sent check your email')
                return redirect(url_for('rlogin'))
        else:
            flash('Invalid email id')
            return render_template('rforgot.html')
    return render_template('rforgot.html')
@app.route('/rreset/<token>',methods=['GET','POST'])
def rreset(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        email=serializer.loads(token,salt=salt2,max_age=3600)
    except Exception as e:
        print(e)
        # abort(404,'Link Expired')

    if request.method=='POST':
        email=request.form['email']
        newpassword=request.form['npassword']
        confirmpassword=request.form['cpassword']
        if newpassword==confirmpassword:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update benf set password=%s where email=%s',[newpassword,email])
            mydb.commit()
            flash('Reset Successful')
            return redirect(url_for('rlogin'))
        else:
            flash('Passwords mismatched')
            return render_template('newpassword.html')
    return render_template('newpassword.html')
@app.route('/rlogout')
def rlogout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('rlogin'))
    else:
        return redirect(url_for('rlogin'))
if __name__ =="__main__":
    app.run()
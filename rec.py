from flask import Flask,render_template,url_for,request,session,flash,redirect,abort
from flask_session import Session
from smail import sendmail
from keys import secret_key,salt,salt2
from itsdangerous import URLSafeTimedSerializer
from tokens import token
import mysql.connector
app=Flask(__name__)
app.secret_key=secret_key
mydb=mysql.connector.connect(host='localhost',user='root',password='heez@1183',db='fwr')
@app.route('/')
#------------Donor----------------->
def index():
    return render_template('index.html')
@app.route('/rregistration',methods=['GET','POST'])
def rregistration():#--------------------            Reciever                --------->
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
            return redirect(url_for('login'))
    return render_template('rregistration.html')
@app.route('/rconfirm/<token>')
def rconfirm(token): #------------Donor----------------->
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        email=serializer.loads(token,salt=salt,max_age=120)
    except Exception as e:
        abort(404,'Link expired')
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email_status from benf where email=%s',[email])
        status=cursor.fetchone()[0]
        cursor.close()
        if status=='confirmed':
            flash('Email already confirmed')
            return redirect(url_for('login'))
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
            return redirect(url_for('homepage'))
        else:
            subject='Email Confirmation'
            confirm_link=url_for('confirm',token=token(email,salt),_external=True)
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
        cursor.execute('select count(*) from  benf where email=%s',[email])
        count=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('SELECT email_status from  benf where email=%s',[email])
            status=cursor.fetchone()[0]
            cursor.close()
            if status!='confirmed':
                flash('Please Confirm your email first')
                return render_template('rforgot.html')
            else:
                subject='Forget Password'
                confirm_link=url_for('reset',token=token(email),salt=salt2,_external=True)
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
        email=serializer.loads(token,salt=salt2,max_age=360)
    except:
        abort(404,'Link Expired')
    else:
        if request.method=='POST':
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
app.run(use_reloader=True,debug=True)
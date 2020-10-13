from flask import Flask,render_template,g,request,session,redirect,url_for
from database import get_db
from werkzeug.security import generate_password_hash,check_password_hash
import os
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g,'sqlite_db'):
        g.sqlite_db.close()


def get_current_user():
    if 'user' in session:
        user = session['user']
        db = get_db()
        user_cur = db.execute("SELECT ID, NAME,PASSWORD,EXPERT,ADMIN FROM USERS WHERE NAME = ?",[user])
        user_result = user_cur.fetchone()      
    else:
        user = None
        user_result = None

    return user_result
    

@app.route('/')
def index():
    # NE ASIGURAM CA USERUL EXISTA IN SESIUNE
    user = get_current_user()
    db = get_db()
    answered_cur = db.execute('SELECT Q.ID as question_id,Q.QUESTION_TEXT,A.NAME as asker_name,E.NAME as expert_name FROM QUESTIONS Q JOIN USERS AS A  ON A.ID = Q.ASKEB_BY_ID JOIN USERS AS E ON E.ID = Q.EXPERT_ID WHERE QUESTION_TEXT IS NOT NULL')
    answered_result = answered_cur.fetchall()
    return render_template('home.html',user = user, answered_result=answered_result)

@app.route('/login',methods=['GET','POST'])
def login():
    user = get_current_user()
    isNotOk = False
    if request.method == 'POST':
        db = get_db()
        name = request.form['name']
        password = request.form['password']
        
        user_cur = db.execute("SELECT ID, NAME,PASSWORD FROM USERS WHERE NAME = ?",[name])
        user_result = user_cur.fetchone()
        if user_result is None:
            isNotOk = True
        else:
            if check_password_hash(user_result['PASSWORD'], password): # se compara parola din baza de date cu cea din form
                #se creaza o sesiune cu userul din baza de date
                session['user'] = user_result['NAME']
                return redirect(url_for('index'))
            else:
                isNotOk = True

    return render_template('login.html',isNotPassOk=isNotOk,user = user)


@app.route('/question/<question_id>')
def question(question_id):
    user = get_current_user()
    db = get_db()
    question_cur = db.execute('SELECT Q.QUESTION_TEXT,Q.ANSWER_TEXT,A.NAME as asker_name,E.NAME as expert_name FROM QUESTIONS Q JOIN USERS AS A  ON A.ID = Q.ASKEB_BY_ID JOIN USERS AS E ON E.ID = Q.EXPERT_ID WHERE Q.ID = ?',[question_id])
    question_result = question_cur.fetchone()
    return render_template('question.html',user = user,question_result = question_result)


@app.route('/register',methods=['GET','POST'])
def register():
    user = get_current_user()
    isNotPassOk = False
    isUserExist = False
    if request.method == 'POST':
        db = get_db()
        name = request.form['name']
        simple_password = request.form['password']

        existingUserCur = db.execute('SELECT ID FROM USERS WHERE NAME = ?',[name])
        existingUserRes = existingUserCur.fetchone()
        if existingUserRes: #asa facem sa intoarcem sa nu permitem trecerea mai departe
            isUserExist = True
            return render_template('register.html', isNotPassOk = isNotPassOk,user = user,isUserExist = isUserExist)
                
        password = generate_password_hash(request.form['password'],method='sha256')
        if (len(simple_password) < 8) or (simple_password ==''):
            isNotPassOk = True
        else:
            db.execute('INSERT INTO USERS(NAME,PASSWORD,EXPERT,ADMIN) VALUES (?,?,?,?)',[name,password,'0','0'])
            db.commit()
            session['user'] = name
            return redirect(url_for('index'))
            
    return render_template('register.html', isNotPassOk = isNotPassOk,user = user)


@app.route('/unanswered')
def unanswered():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if user['expert'] == 0: # verific sesiunea daca e admin sau nu sa ii dau voie
        return redirect(url_for('index'))
    isNullQuestions = False
    db = get_db()
    question_cur = db.execute('SELECT Q.ID,Q.QUESTION_TEXT,Q.ASKEB_BY_ID, U.NAME FROM QUESTIONS Q \
                                LEFT JOIN USERS U ON U.ID = Q.ASKEB_BY_ID \
                                WHERE ANSWER_TEXT IS NULL AND EXPERT_ID = ?',[user['id']])
    experts_result = question_cur.fetchall()
    if experts_result is None:
        isNullQuestions = True
    # to do de terminat functia asta sa afisez in html rezultatul si sa pot arata de cine a fost intrebat
    return render_template('unanswered.html',user = user, experts_result = experts_result, isNullQuestions = isNullQuestions)

@app.route('/users')
def users():
    user = get_current_user()
    db = get_db()
    if not user:
        return redirect(url_for('login'))

    if user['admin'] == 0: # verific sesiunea daca e admin sau nu sa ii dau voie
        return redirect(url_for('index'))

    user_cur = db.execute('SELECT * FROM USERS')
    user_result = user_cur.fetchall()
    return render_template('users.html',user = user,user_result = user_result)

@app.route('/answer/<question_id>', methods= ['GET','POST'])
def answer(question_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if user['expert'] == 0: # verific sesiunea daca e admin sau nu sa ii dau voie
        return redirect(url_for('index'))
    db = get_db()
    question_cur = db.execute('SELECT ID,QUESTION_TEXT FROM QUESTIONS WHERE ID = ?',[question_id])
    question_result = question_cur.fetchone()
    if request.method == 'POST':
        answer = request.form['answer']
        db.execute('UPDATE QUESTIONS SET ANSWER_TEXT = ? WHERE ID = ?',[answer,question_id])
        db.commit()
        return redirect(url_for('unanswered'))


    return render_template('answer.html',user = user,question_result = question_result)

@app.route('/ask',methods=['GET','POST'])
def ask():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        question = request.form['question']
        expert   = request.form['expert'] 
        
        db.execute('INSERT INTO QUESTIONS(QUESTION_TEXT, ASKEB_BY_ID, EXPERT_ID) VALUES(?, ?, ?)',[question,user['id'],expert])
        db.commit()
        return redirect(url_for('index'))
    ask_cur = db.execute('SELECT ID, NAME FROM USERS WHERE EXPERT = 1')
    ask_result = ask_cur.fetchall()
    return render_template('ask.html',user = user,ask= ask_result)



@app.route('/promote/<id>')#asta e pasat in url_for in html 
def promote(id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if user['admin'] == 0: # verific sesiunea daca e admin sau nu sa ii dau voie
        return redirect(url_for('index'))
    db = get_db()
    db.execute('UPDATE USERS SET EXPERT = 1 WHERE ID = ?',[id])
    db.commit()
    return redirect(url_for('users'))

@app.route('/logout')
def logout():
    
    session.pop('user',None) #asa delogam userul de la sesiune
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
# from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)


app.config['SECRET_KEY'] = 'you-will-never-guess'


# Articles

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MYSQL
mysql = MySQL(app)

# Articles = Articles()

# Index


@app.route('/')
def index():
    return render_template('home.html')

# About


@app.route('/about')
def about():
    return render_template('about.html')

# Artiles
@app.route('/articles')
def articles():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    cur.close()


# Single Artile
@app.route('/article/<string:id>/')
def article(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM articles where id = %s",[id])
    article = cur.fetchone()
    return render_template('article.html', article=article)

# 用户注册类
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('UserName', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message="密码不对")
    ])
    confirm = PasswordField('Confirm Password')

# 用户注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # 数据库操作
        cur = mysql.connection.cursor()  # 创建游标
        sql = "INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)"
        cur.execute(sql, (name, email, username, password))  # 插入数据
        mysql.connection.commit()   # 保存
        cur.close()  # 关闭

        flash('注册成功', 'success')
        return redirect(url_for('index'))

    return render_template('register.html', form=form)

# 用户登陆
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 获取文件信息
        username = request.form['username']
        password_candidate = request.form['password']

        cur = mysql.connection.cursor()  # 创建游标
        result = cur.execute(
            "SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # 获取数据库密码hash
            data = cur.fetchone()
            password = data['password']

            # 密码比较
            if sha256_crypt.verify(password_candidate, password):
                # app.logger.info('password matcher')
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')


# 检查登陆
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# 退出
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
    cur.close()

    return render_template('dashboard.html')

# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #插入数据
        cur = mysql.connection.cursor()
        sql = "INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)"
        cur.execute(sql, (title, body, session['username'])) 
        mysql.connection.commit()
        cur.close()

        flash('Article Created', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_article.html',form = form)

# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # 从数据库获取对应id的值
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM articles WHERE id = %s", [id]) #获取ID
    article = cur.fetchone()
    cur.close()

    # 填表
    form = ArticleForm(request.form)
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        #从表单拿数据准备存入数据库
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


# 删除事件
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM articles WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))
    
if __name__ == "__main__":
    app.run(debug=True)

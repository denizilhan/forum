from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.utils import secure_filename

# Kullanıcı giriş decoratoru


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:

            return f(*args, **kwargs)
        else:
            flash("Giriş Yapmadan Nereye?", "danger")
            return redirect(url_for("login"))
    return decorated_function
# Kullanıcı kayıt formu


class RegisterForm(Form):
    name = StringField("İsim Soyisim", validators=[
                       validators.length(min=5, max=20), validators.DataRequired()])
    username = StringField("Kullanıcı Adı", validators=[
                           validators.length(min=5, max=30), validators.DataRequired()])
    email = StringField("Email Adresi", validators=[validators.Email(
        message="Lütfen Geçerli bir email adresi girin")])
    password = PasswordField("Parola ", validators=[
        validators.DataRequired(message="Lütfen bir parola belirleyin"),
        validators.EqualTo(fieldname="confirm", message="Parolanız uyuşmuyor")])
    confirm = PasswordField("Parola Doğrula")


class LoginFrom(Form):
    username = StringField("Kullanıcı Adını")
    password = PasswordField("Parola")


app = Flask(__name__)
mysql = MySQL(app)


app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "admin"
app.config['MYSQL_PASSWORD'] = "utlXL_/p}c6}I;x+"
app.config['MYSQL_DB'] = "python"
app.config['MYSQL_CURSORCLASS'] = "DictCursor"
app.secret_key = "123"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "SELECT * FROM articles WHERE author = %s"

    result = cursor.execute(sorgu, (session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles=articles)
    else:
        return render_template("dashboard.html")
# Kayıt olma
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(sorgu, (name, email, username, password))

        mysql.connection.commit()
        cursor.close()
        flash("Kayıt Tamamlandı", "success")
        flash('You are now registered and can login, thank you', 'success')
        return redirect(url_for('login'))
    else:
        return render_template('register.html', form=form)


@app.route("/articles/<string:id>")
def detail(id):
    return "Article Id:" + id

# login işlemi
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginFrom(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "SELECT * FROM users WHERE username = %s"

        result = cursor.execute(sorgu, (username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered, real_password):
                flash("Başarıyla Giriştin", "success")

                session['logged_in'] = True
                session['username'] = username

                return redirect(url_for("index"))
            else:
                flash(("Parolanı Bilmiyorsun Daha"))
                return redirect(url_for("login"))
        else:
            flash("Tanıdım da Şu An Şeapamadım  ", "danger")
            return redirect(url_for("login"))
    return render_template("login.html", form=form)

# Detay sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()

    sorgu = "SELECT * FROM articles WHERE id = %s"

    result = cursor.execute(sorgu, (id,))

    if result > 0:
        article = cursor.fetchone()

        return render_template("article.html", article=article)
    else:
        return render_template("article.html")
# logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/addarticle", methods=["GET", "POST"])
def addarticle():
    form = ArticleFrom(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu, (title, session["username"], content))

        mysql.connection.commit()
        cursor.close()
        flash("Makale de Yüklermiş", "success")
        return redirect(url_for('dashboard'))

    return render_template("addarticle.html", form=form)
# Makale Güncelleme
@app.route("/edit/<string:id>", methods=["GET", "POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()

        sorgu = "SELECT * FROM articles WHERE id = %s AND author = %s"

        result = cursor.execute(sorgu, (id, session["username"]))

        if result == 0:
            flash("Böyle bir makale yok yada sen dokanamıyorsun")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleFrom()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html", form=form)

    else:
        # POST REQUEST
        form = ArticleFrom(request.form)

        newTitle = form.title.data
        newContent = form.content.data

        sorgu = "UPDATE articles SET title = %s, content = %s WHERE id = %s"

        cursor = mysql.connection.cursor()

        cursor.execute(sorgu, (newTitle, newContent, id))

        mysql.connection.commit()

        flash("Makale Güncellendi", "success")

        return redirect(url_for("dashboard"))


# Makale silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "SELECT * FROM articles WHERE author = %s AND id = %s"

    result = cursor.execute(sorgu, (session["username"], id))

    if result > 0:
        sorgu2 = "DELETE FROM articles WHERE id = %s"
        cursor.execute(sorgu2, (id,))
        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok yada sen silmeyi beceremedin", "danger")
        return redirect(url_for("index"))

# Makale form


class ArticleFrom(Form):
    title = StringField("Makale Başlığı", validators=[
                        validators.Length(min=5, max=100)])
    content = TextAreaField("Makale İçeriği", validators=[
                            validators.Length(min=10)])

# Makaleleri okuma
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()

    sorgu = "SELECT * FROM articles"

    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles=articles)
    else:
        return render_template("articles.html")

# Arama URL
@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()

        sorgu = "SELECT * FROM articles WHERE title LIKE '%" + keyword + "%'"

        result = cursor.execute(sorgu)

        if result == 0:
            flash("Aranan kelimeye uygun makale bulunamadı")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()

            return render_template("articles.html", articles=articles)



if __name__ == "__main__":
    app.run(debug=True)

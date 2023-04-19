from flask import Flask,request, render_template, redirect, url_for, flash,abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm,RegisterForm,LoginForm,CommentForm
from flask_gravatar import Gravatar
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihuhuhohugü9fröt8zoiöhBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#Gravatar
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)




class Comment(db.Model):
    __tablename__= "comments"
    id = db.Column(db.Integer,primary_key=True)
    text = db.Column(db.String,nullable=False)

    comment_author = db.Column(db.String,nullable=False)
    #parent_post=db.Column(db.String,nullable=False)
    #relationship with user
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))#
    comment = relationship("User", back_populates="comments")
    #child
    blog_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id")) #
    written_comment = relationship("BlogPost",back_populates="user_comment") #same as parent_post

    #relationship with blog posts
class BlogPost(UserMixin,db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
   # author = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    # n in 1 zu n beziehung child
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")

    user_comment = relationship("Comment",back_populates="written_comment")



class User(UserMixin,db.Model):
    __tablename__="users"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True,nullable=False)
    password = db.Column(db.String(100))
    #parent 1 zu n Beziehung
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment",back_populates="comment")

    #parent



db.create_all()
login_manager= LoginManager()
login_manager.init_app(app)
#ist keine user klasse hier daher wird auch kein user gefunden  User = RegiderForm



#Decorator Function Admin
def is_admin(function):
    @wraps(function) # does that the function doesn´t loose their functionality
    def admin(*args,**kwargs):
        if current_user.id!=1:
            return abort(403)
        return function(*args,**kwargs) # if this is triggerd the normal funtction with all kwargs and args is run

    return admin



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts, logged_in=current_user)


@app.route('/register',methods=["GET","POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit(): #schauen ob submit gedrückt wurde
        email = form.email.data
        if User.query.filter_by(email=form.email.data).first():
            flash("Email wurde schon einaml verwendet.Bitte melden Sie sich an")
            print(User.query.filter_by(email=form.email.data).first())
            return redirect(url_for("login"))

        #erstellt kein user

        #funktioniert soweit nur noch flash nachrichten, wenn user schon vorhanden sind fehlen noch


        password_hashed = generate_password_hash(password=form.password.data,method="pbkdf2:sha256",salt_length=8)
        new_user = User (
            email = email ,
            password = password_hashed,
            name = form.name.data,
            )

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)

        return redirect(url_for("get_all_posts"))

    return render_template("register.html",form=form,logged_in=current_user)




@app.route('/login',methods=["POST","GET"])
def login():

    form = LoginForm()

    if form.validate_on_submit():

        password_plain = form.password.data
        email = form.email.data
        #warum nur hier email = email und nicht form.email.data
        user = User.query.filter_by(email=email).first() # blog post db hat kein email
        #durch email benutzer suchen
        if not user:
            flash("Die eingegebene Email, stimmt mit keinem Account überein. Bitte erstellen Sie einen")
            return redirect(url_for("login"))







        elif not check_password_hash(user.password,password_plain):
            flash("Incorrect Password")
            return redirect(url_for("login"))

        else:
            login_user(user)

            return redirect(url_for("get_all_posts"))




    return render_template("login.html",form=form,logged_in=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))

#only authenticated users are allowed to make comments otherwise redirect them to login flash message
@app.route("/post/<int:post_id>",methods=["GET","POST"])
def show_post(post_id):

    requested_post = BlogPost.query.get(post_id)

    form = CommentForm()

    if form.validate_on_submit():
        if not current_user.is_authenticated():
            flash("You have to login or register to send comments")
            return redirect(url_for("login"))


        new_comment=Comment(
            text= form.comment.data,
            comment_author=current_user,
            parent_post=requested_post,
        )
        db.session.add(new_comment)
        db.session.commit()
    #was macht das allgemein filter_by was


    #warum in post.comments wie kann post ein objekt sein und comments das attribut dazu
    return render_template("post.html",form=form,logged_in=current_user)
        #dann ist was



@app.route("/about")
def about():
    return render_template("about.html",logged_in=current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html",logged_in=current_user)

@login_required
@is_admin
@app.route("/new-post")
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form,logged_in=current_user)


@app.route("/edit-post/<int:post_id>")
@is_admin

def edit_post(post_id):
    post = User.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form,logged_in=current_user)


@is_admin
@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, redirect, request, make_response, jsonify, url_for
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from wtforms import IntegerField, StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, length
from data import dbSession
from data.users import User
from data.mistakes import Mistake
from data.languages import Language
from modules import speller, translator
import json
import copy


app = Flask(__name__)
app.config['SECRET_KEY'] = 'Kr,}je-c+45m{G4=8y&t'

loginManager = LoginManager()
loginManager.init_app(app)


class RegisterForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    passwordRepeat = PasswordField('Password repeat', validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired()])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')


class BeautifierForm(FlaskForm):
    text = TextAreaField('Text to beautify', validators=[DataRequired(), length(max=10000)])
    submit = SubmitField('Beautify')


@loginManager.user_loader
def loadUser(id):
    session = dbSession.createSession()
    return session.query(User).get(id)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.passwordRepeat.data:
            return render_template('register.html', title='Register', form=form, message='Different passwords')
        session = dbSession.createSession()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Register', form=form, message='User already exists')
        user = User(email=form.email.data,
                    surname=form.surname.data,
                    name=form.name.data,
                    age=form.age.data)
        user.setPassword(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/')
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = dbSession.createSession()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.checkPassword(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect('/')
        return render_template('login.html', form=form, title='Login', message='Wrong email or password')
    return render_template('login.html', form=form, title='Login')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/', methods=['GET', 'POST'])
def mainPage():
    form = BeautifierForm()
    if form.validate_on_submit():
        data = json.dumps({'text': form.text.data, 'mistakes': speller.getMistakes(form.text.data)})
        return redirect(url_for('result', data=data))
    return render_template('main.html', title='Beautifier', form=form)


@app.route('/result')
def result():
    data = json.loads(request.args['data'])
    mistakes = data['mistakes']
    text = data['text']
    corrected = copy.copy(text)
    delta = 0
    tablelist = []
    for m in mistakes:
        word = m['s'][0]
        lang = translator.getLanguage(word)
        session = dbSession.createSession()
        language = session.query(Language).filter(Language.acronym == lang).first()
        if language is None:
            language = Language(acronym=lang)
            session.add(language)
            session.commit()
        wrong = text[m['pos']:m['pos'] + m['len']]
        corrected = corrected[:m['pos'] + delta] + word + corrected[m['pos'] + m['len'] + delta:]
        delta += len(word) - len(wrong)
        session = dbSession.createSession()
        mistake = session.query(Mistake).filter(Mistake.name == word.lower()).first()
        if mistake is None:
            mistake = Mistake(name=word.lower(), count=0, language=language.id)
        mistake.count += 1
        if current_user.is_authenticated:
            current_user.mistakes.append(mistake)
            session.merge(current_user)
        else:
            session.add(mistake)
        session.commit()
        tablelist.append({'wrong': wrong.lower(),
                          'correct': word.lower(),
                          'pos': m['pos'],
                          'lang': lang})

    return render_template('result.html', title='Result', text=corrected, tablelist=tablelist)


def main():
    dbSession.globalInit('db/ortho.sqlite')
    app.run()


if __name__ == '__main__':
    main()

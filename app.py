from flask import Flask, render_template, redirect, request, make_response, jsonify, url_for
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_googlecharts import GoogleCharts, PieChart, ColumnChart
from wtforms import IntegerField, StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, length
from data import dbSession
from data.users import User
from data.mistakes import Mistake
from data.languages import Language
from modules import speller, translator
from collections import defaultdict
import json
import copy
import pymorphy2

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Kr,}je-c+45m{G4=8y&t'
charts = GoogleCharts(app)

morph = pymorphy2.MorphAnalyzer()

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
        wrong = text[m['pos']:m['pos'] + m['len']]
        normal = morph.parse(word)[0].normal_form
        lang = translator.getLanguage(word)
        session = dbSession.createSession()
        language = session.query(Language).filter(Language.acronym == lang).first()
        if language is None:
            language = Language(acronym=lang)
            session.add(language)
            session.commit()
        corrected = corrected[:m['pos'] + delta] + word + corrected[m['pos'] + m['len'] + delta:]
        delta += len(word) - len(wrong)
        session = dbSession.createSession()
        mistake = session.query(Mistake).filter(Mistake.name == normal).first()
        if mistake is None:
            mistake = Mistake(name=normal, count=0, language=language.id)
            session.add(mistake)
        mistake.count += 1
        if current_user.is_authenticated:
            user = session.query(User).get(current_user.id)
            user.mistakes.append(mistake)
            session.merge(user)
        session.commit()
        tablelist.append({'wrong': wrong.lower(),
                          'correct': word.lower(),
                          'pos': m['pos'],
                          'lang': lang})
    return render_template('result.html', title='Result', text=corrected, tablelist=tablelist)


@app.route('/stats')
def globalStats():
    session = dbSession.createSession()
    mistakes = session.query(Mistake).all()
    users = session.query(User).all()
    languages = session.query(Language).all()
    popularityChart = PieChart('popularity', options={'title': 'Mistakes popularity',
                                                      'height': 400})
    popularityData = getPopularityData(mistakes)
    for column in popularityData['columns']:
        popularityChart.add_column(*column)
    popularityChart.add_rows(popularityData['rows'])
    charts.register(popularityChart)
    ageChart = ColumnChart('age', options={'title': 'Mistakes by age',
                                           'height': 400})
    ageData = getAgeData(mistakes, users)
    for column in ageData['columns']:
        ageChart.add_column(*column)
    ageChart.add_rows(ageData['rows'])
    charts.register(ageChart)
    languageChart = PieChart('language', options={'title': 'Mistakes by language',
                                                  'height': 400})
    languagesData = getLanguagesData(mistakes)
    for column in languagesData['columns']:
        languageChart.add_column(*column)
    languageChart.add_rows(languagesData['rows'])
    charts.register(languageChart)
    return render_template('global_stats.html', title='Stats', mistakes=mistakes, languages=languages)


@app.route('/local_stats')
@login_required
def localStats():
    session = dbSession.createSession()
    mistakes = current_user.mistakes
    languages = session.query(Language).all()
    popularityChart = PieChart('local_popularity', options={'title': 'Mistakes popularity',
                                                            'height': 400})
    popularityData = getPopularityData(mistakes)
    for column in popularityData['columns']:
        popularityChart.add_column(*column)
    popularityChart.add_rows(popularityData['rows'])
    charts.register(popularityChart)
    languageChart = PieChart('local_language', options={'title': 'Mistakes by language',
                                                        'height': 400})
    languagesData = getLanguagesData(mistakes)
    for column in languagesData['columns']:
        languageChart.add_column(*column)
    languageChart.add_rows(languagesData['rows'])
    charts.register(languageChart)
    return render_template('local_stats.html', title='Stats', mistakes=mistakes, languages=languages)


def getPopularityData(mistakes):
    return {'columns': [['string', 'Word'], ['number', 'Count']],
            'rows': [[mistake.name, mistake.count] for mistake in mistakes]}


def getAgeData(mistakes, users):
    ages = defaultdict(int)
    for user in users:
        ages[user.age // 10] += len(user.mistakes)
    return {'columns': [['string', 'Age range'], ['number', 'Count']],
            'rows': [[f'{item[0] * 10} - {item[0] * 10 + 9}', item[1]] for item in ages.items()]}


def getLanguagesData(mistakes):
    session = dbSession.createSession()
    langs = defaultdict(int)
    for mistake in mistakes:
        langs[mistake.language] += mistake.count
    return {'columns': [['string', 'Language'], ['number', 'Count']],
            'rows': [[session.query(Language).get(item[0]).acronym, item[1]] for item in langs.items()]}


def main():
    dbSession.globalInit('db/ortho.sqlite')
    app.run()


if __name__ == '__main__':
    main()

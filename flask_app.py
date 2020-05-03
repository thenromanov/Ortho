from flask import Flask, render_template, redirect, request, make_response, jsonify, url_for
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_googlecharts import GoogleCharts, PieChart, ColumnChart
from flask_restful import Api
from wtforms import IntegerField, StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, length
from data import dbSession
from data.users import User
from data.mistakes import Mistake
from data.languages import Language
from data.association import Association
from modules import speller, translator
from collections import defaultdict
from secrets import token_urlsafe
from api import mistakesResources, statisticsResources, beautifierResources
import json
import copy
import pymorphy2

app = Flask(__name__)
app.config['SECRET_KEY'] = token_urlsafe(16)  # Генерируем защитный ключ
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/ortho.db'
charts = GoogleCharts(app)  # Инициализируем диаграммы
api = Api(app)  # Инициализируем API

morph = pymorphy2.MorphAnalyzer()  # Инициализируем модуль морфологии

loginManager = LoginManager()
loginManager.init_app(app)


class RegisterForm(FlaskForm):
    ''' Форма регистрации '''
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    passwordRepeat = PasswordField('Password repeat', validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired()])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    ''' Форма входа '''
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')


class BeautifierForm(FlaskForm):
    ''' Форма корректора текста '''
    text = TextAreaField('Text to beautify', validators=[DataRequired(), length(max=10000)])
    submit = SubmitField('Beautify')


@loginManager.user_loader
def loadUser(id):
    session = dbSession.createSession()
    return session.query(User).get(id)


@app.route('/register', methods=['GET', 'POST'])
def register():
    ''' Страница регистрации пользователя'''
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
                    age=form.age.data,
                    token=token_urlsafe(16))
        user.setPassword(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/')
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    ''' Страница входа пользователя '''
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


@app.route('/token')
@login_required
def tokenPage():
    ''' Старница отображения индивидуального токена для работы с API '''
    return render_template('token.html')


@app.route('/', methods=['GET', 'POST'])
def mainPage():
    ''' Базовая страница корректора '''
    form = BeautifierForm()
    if form.validate_on_submit():
        ''' При запуске корректора данные проверяются Яндекс.Спеллером на ошибки
            и передаются на страницу отображения результатов проверки в формате json'''
        data = json.dumps({'text': form.text.data, 'mistakes': speller.getMistakes(form.text.data)})
        return redirect(url_for('result', data=data))
    return render_template('main.html', title='Beautifier', form=form)


@app.route('/result')
def result():
    ''' Страница отображения результатов проверки текста '''
    data = json.loads(request.args['data'])  # Данные, переданные корректором
    mistakes = data['mistakes']
    text = data['text']
    corrected = copy.copy(text)
    delta = 0
    tablelist = []
    for m in mistakes:
        correct = m['s'][0]  # Исправленное слово
        wrong = text[m['pos']:m['pos'] + m['len']]  # Ошибочное слово
        normal = morph.parse(correct)[0].normal_form  # Исправленное слово в начальной форме
        # Язык слова. Определяется API Яндекс.Переводчика
        langAcronym = translator.getLanguage(correct)
        corrected = corrected[:m['pos'] + delta] + correct + \
            corrected[m['pos'] + m['len'] + delta:]  # Исправление начального текста
        # Эта переменная хранит в себе изменение длины текста для правильного корректирования
        delta += len(correct) - len(wrong)
        session = dbSession.createSession()
        language = session.query(Language).filter(Language.acronym == langAcronym).first()
        if not language:
            # Если язык незнакомый, добавим его в БД
            language = Language(acronym=langAcronym)
            session.add(language)
        mistake = session.query(Mistake).filter(Mistake.name == normal).first()
        if not mistake:
            # Если ошибка незнакомая, добавим ее в БД
            mistake = Mistake(name=normal, count=0, language=language.id)
            session.add(mistake)
        mistake.count += 1
        if current_user.is_authenticated:
            # Если пользователь аутентифицирован, то запишем эту ошибку в ассоциативную БД
            association = session.query(Association).filter(
                Association.mistake == mistake.id, Association.user == current_user.id).first()
            if not association:
                association = Association(mistake=mistake.id, count=0)
                user = session.query(User).get(current_user.id)
                user.mistakes.append(association)
            association.count += 1
        session.commit()
        tablelist.append({'wrong': wrong.lower(),
                          'correct': correct.lower(),
                          'pos': m['pos'],
                          'lang': langAcronym})
    return render_template('result.html', title='Result', text=corrected, tablelist=tablelist)


@app.route('/stats')
def globalStats():
    ''' Страница с глобальной статистикой использования сайта '''
    session = dbSession.createSession()
    mistakes = session.query(Mistake).all()
    tablelist = []
    for mistake in mistakes:
        language = session.query(Language).get(mistake.language)
        tablelist.append({'name': mistake.name,
                          'count': mistake.count,
                          'lang': language.acronym})
    # Круговая диаграмма частоты ошибок в словах
    popularityChart = PieChart('popularity', options={'title': 'Mistakes popularity',
                                                      'height': 400})
    popularityChart.add_column('string', 'Word')
    popularityChart.add_column('number', 'Count')
    popularityChart.add_rows([[item['name'], item['count']] for item in tablelist])
    charts.register(popularityChart)
    # Столбчатая диаграмма количества ошибок в зависимости от возраста в диапозоне 10 лет
    ageChart = ColumnChart('age', options={'title': 'Mistakes by age',
                                           'height': 400})
    ages = defaultdict(int)
    for user in session.query(User).all():
        for mistake in user.mistakes:
            ages[user.age // 10] += mistake.count
    ageChart.add_column('string', 'Age range')
    ageChart.add_column('number', 'Count')
    ageChart.add_rows([[f'{item[0] * 10} - {item[0] * 10 + 9}', item[1]]
                       for item in sorted(ages.items(), key=lambda x: x[0])])
    charts.register(ageChart)
    # Круговая диаграмма количества ошибок в зависимости от языка
    languageChart = PieChart('language', options={'title': 'Mistakes by language',
                                                  'height': 400})
    langs = defaultdict(int)
    for item in tablelist:
        langs[item['lang']] += item['count']
    languageChart.add_column('string', 'Language')
    languageChart.add_column('number', 'Count')
    languageChart.add_rows([[item[0], item[1]] for item in langs.items()])
    charts.register(languageChart)
    return render_template('global_stats.html', title='Stats', mistakes=tablelist)


@app.route('/local_stats')
@login_required
def localStats():
    ''' Страница локальной статистики для зарегестрированный пользователей '''
    session = dbSession.createSession()
    user = session.query(User).get(current_user.id)
    tablelist = []
    for association in user.mistakes:
        mistake = session.query(Mistake).get(association.mistake)
        language = session.query(Language).get(mistake.language)
        tablelist.append({'name': mistake.name,
                          'count': association.count,
                          'lang': language.acronym})
    # Круговая диаграмма частоты ошибок в словах
    popularityChart = PieChart('local_popularity', options={'title': 'Mistakes popularity',
                                                            'height': 400})
    popularityChart.add_column('string', 'Word')
    popularityChart.add_column('number', 'Count')
    popularityChart.add_rows([[item['name'], item['count']] for item in tablelist])
    charts.register(popularityChart)
    # Круговая диаграмма количества ошибок в зависимости от языка
    languageChart = PieChart('local_language', options={'title': 'Mistakes by language',
                                                        'height': 400})
    langs = defaultdict(int)
    for item in tablelist:
        langs[item['lang']] += item['count']
    languageChart.add_column('string', 'Language')
    languageChart.add_column('number', 'Count')
    languageChart.add_rows([[item[0], item[1]] for item in langs.items()])
    charts.register(languageChart)
    return render_template('local_stats.html', title='Local stats', mistakes=tablelist)


def main():
    dbSession.globalInit('db/ortho.db')
    api.add_resource(mistakesResources.MistakesResouce, '/api/mistakes')
    api.add_resource(statisticsResources.StatisticsResource, '/api/statistics')
    api.add_resource(beautifierResources.BeautifierResource, '/api/beautifier')
    app.run()


if __name__ == '__main__':
    main()

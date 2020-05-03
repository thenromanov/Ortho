from flask import jsonify
from flask_restful import abort, Resource
from data import dbSession
from data.users import User
from data.mistakes import Mistake
from data.languages import Language
from .statisticsParser import parser
from collections import defaultdict


class StatisticsResource(Resource):
    def get(self):
        args = parser.parse_args()
        session = dbSession.createSession()
        tablelist = []
        if args['type'] == 'age':
            ages = defaultdict(int)
            for user in session.query(User).all():
                for mistake in user.mistakes:
                    ages[user.age] += mistake.count
            for item in ages.items():
                tablelist.append({item[0]: item[1]})
        elif args['type'] == 'lang':
            langs = defaultdict(int)
            for mistake in session.query(Mistake).all():
                language = session.query(Language).get(mistake.language)
                langs[language.acronym] += mistake.count
            for item in langs.items():
                tablelist.append({item[0]: item[1]})
        return tablelist

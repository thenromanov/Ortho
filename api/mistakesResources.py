from flask import jsonify
from flask_restful import abort, Resource
from data import dbSession
from data.users import User
from data.mistakes import Mistake
from data.languages import Language
from .mistakesParser import parser


class MistakesResouce(Resource):
    def get(self):
        args = parser.parse_args()
        session = dbSession.createSession()
        tablelist = []
        if args['token']:
            user = session.query(User).filter(User.token == args['token']).first()
            if not user:
                abort(404, message='Wrong token')
            for association in user.mistakes:
                mistake = session.query(Mistake).get(association.mistake)
                lang = session.query(Language).get(mistake.language)
                tablelist.append({'name': mistake.name,
                                  'count': association.count,
                                  'lang': lang.acronym})
        else:
            for mistake in session.query(Mistake).all():
                lang = session.query(Language).get(mistake.language)
                tablelist.append({'name': mistake.name,
                                  'count': mistake.count,
                                  'lang': lang.acronym})
        return jsonify({'mistakes': tablelist})

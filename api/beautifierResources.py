from flask import jsonify
from flask_restful import abort, Resource
from data import dbSession
from data.mistakes import Mistake
from data.languages import Language
from modules import speller, translator
from .beautifierParser import parser
import copy
import pymorphy2


class BeautifierResource(Resource):
    def get(self):
        morph = pymorphy2.MorphAnalyzer()
        args = parser.parse_args()
        text = args['text']
        mistakes = speller.getMistakes(text)
        corrected = copy.copy(text)
        delta = 0
        tablelist = []
        for m in mistakes:
            correct = m['s'][0]
            wrong = text[m['pos']:m['pos'] + m['len']]
            normal = morph.parse(correct)[0].normal_form
            langAcronym = translator.getLanguage(correct)
            corrected = corrected[:m['pos'] + delta] + \
                correct + corrected[m['pos'] + m['len'] + delta:]
            delta += len(correct) - len(wrong)
            session = dbSession.createSession()
            language = session.query(Language).filter(Language.acronym == langAcronym).first()
            if not language:
                language = Language(acronym=langAcronym)
                session.add(language)
            mistake = session.query(Mistake).filter(Mistake.name == normal).first()
            if not mistake:
                mistake = Mistake(name=normal, count=0, language=language.id)
                session.add(mistake)
            mistake.count += 1
            session.commit()
            tablelist.append({'wrong': wrong.lower(),
                              'correct': correct.lower(),
                              'pos': m['pos'],
                              'lang': langAcronym})
        return jsonify({'corrected_text': corrected, 'mistakes': tablelist})

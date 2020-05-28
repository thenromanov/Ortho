from flask_restful import reqparse

parser = reqparse.RequestParser()
parser.add_argument('type', choices=['age', 'lang'], required=True)

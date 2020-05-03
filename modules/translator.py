import requests

''' Модуль Яндекс.Переводчика '''


def getLanguage(text):
    url = 'https://translate.yandex.net/api/v1.5/tr.json/detect'
    params = {
        'key': 'trnsl.1.1.20200425T163049Z.df8faea63f55d3a5.63e0685f564e78f2f1731927d759911df3ea9eb8',
        'text': text
    }
    return requests.get(url, params).json()['lang']

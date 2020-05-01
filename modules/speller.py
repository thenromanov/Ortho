import requests


def getMistakes(text):
    url = 'https://speller.yandex.net/services/spellservice.json/checkText'
    params = {
        'text': text,
        'format': 'plain'
    }
    return requests.get(url, params).json()

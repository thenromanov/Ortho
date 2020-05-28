from requests import get

print(get('http://localhost:5000/api/beautifier').json())  # Ошибка - нет текста

# Вернет откорректированный текст и набор ошибок. Данные ошибок добавятся в БД
print(get('http://localhost:5000/api/beautifier', json={'text': 'Прагулка по полисаднику'}).json())

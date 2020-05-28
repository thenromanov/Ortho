from requests import get


print(get('http://localhost:5000/api/statistics').json())  # Ошибка - не указан тип статистики
print(get('http://localhost:5000/api/statistics',
          json={'type': 'lang'}).json())  # Языковая статистика
print(get('http://localhost:5000/api/statistics',
          json={'type': 'age'}).json())  # Возрастная статистика
print(get('http://localhost:5000/api/statistics',
          json={'type': 'count'}).json())  # Ошибка - неверный тип

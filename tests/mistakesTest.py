from requests import get

print(get('http://localhost:5000/api/mistakes').json())  # Глобальная статистика

# Локальная статистика. Для проверки нужно пройти регистрацию и ввести свой токен
print(get('http://localhost:5000/api/mistakes', json={'token': 'usertoken'}).json())

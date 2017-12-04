# Тестовое задание

# Что сделано:
* CRUD для всех сущностей проекта;
* Логика платности события;
* Возможность добавления платного события по стране, провайдеру, проекту;
* Клиент, имитирующий использование API для учета пользовательских событий;
* Итоговая таблица статистики для заданных событий: src/stat.csv;


# Для старта API:
```
pip install -r requirements.txt
python manage.py init_db
python manage.py runserver
```

# Для старта клиента:
```
python manage.py runwriter
```
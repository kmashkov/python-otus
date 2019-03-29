## API Testing

### Краткое описание
Приложение, имитирующее сервис скоринга и предоставлящее Rest API 
для определения собственно скоринга клиента и его интересов.

### Требования
* Python 3.4+
* Memcached
* Redis
* abc
* python-dateutil

### Настройка
При запуске приложения можно передать путь к файлу с настройками кувшы и memcached (-c <store_config_path>).

#### Возможные настройки и настройки по-умолчанию

Redis (используется в качестве основного хранилища):

"store_host": "localhost",

"store_port": 6379,

"store_db": 1,

Memcached (используется в качестве кэша):

"cache_host": "localhost",

"cache_port": 11211

### Запуск тестов
**Модульные тесты:**
```
python3 -m unittest test/unit/test_fields.py
```

**Интеграционные тесты:**

Следует учитывать, что интеграционные тесты проводятся на бд из стандартных настроек.

```
python3 -m unittest test/integration/test_api.py
```

### Запуск сервера скоринга
```
cd src/
python3 api.py [-p <port> -l <log_file_path> -c <store_config_path>]
```
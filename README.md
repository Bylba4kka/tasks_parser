# Парсер заказов с http://freelance.habr.com/ и https://profi.ru/

## Установка зависимостей и запуск
```bash
$ pip3 install virtualenv
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install -r requirements.txt
```

## Запуск программы вручную
```bash
$ source venv/bin/activate
$ python3 main.py [parser_name] [time_span]
``` 

## Параметры запуска
[parser_name] - имя парсера, который нужно запустить. Сейчас доступно habr, fl, freelance, youdo (вначале отправит все задачи, которые найдёт, после будет отправлять те что не отправлял до этого, так что параметр времени можно ставить любой)
[time_span] - количество минут, определяющие, за какой промежуток времени будут отправлены фриланс-задачи. Например, если указать 10, а сейчас 20:00, то будут присланы задачи, опубликованные с 19:50-20:00
Пример использования параметров:
```bash
$ python3 main.py habr 15
``` 
В результате мы получим задачи из freelance.habr.ru за последние 15 минут

## Настройка отправки на сервер
1. Откройте файл, находящийся в корневой папке программы, config.py, если его нет - создайте.
2. Напишите или отредактируйте строку
post_url = 'https://your_url.com'
Для теста можно использовать:
post_url = 'https://444555.requestcatcher.com/test'

## Настройка cron и запуск по расписанию
1. Общие понятия и комманды
1.1 Комманды
```bash
$ crontab -l # выводит список текущих заданий
$ crontab -e # открывает файл заданий для записи
$ crontab -r # удаляет файл задания
$ crontab filename # ПЕРЕЗАПИСЫВАЕТ текущие задания, заданиями из переданного файла
``` 
1.2 Создание задачи для cron
Формат записи:
[минута] [час] [день] [месяц] [день недели] [команда]

1.3 Время
Способы задать время:
*	any value
,	value list separator
-	range of values
/	step values
Примеры:
```
* * * * * -  каждую минуту
*/10 * * * * -  каждую десятую минуту
1,11,21,31,41,51 * * * * -  в первую, одинадцатаю, двадцать первую и т.д. минуту часа
```
Шпаргалка для времени https://crontab.guru/
Если вы хотетите задать интервал минут не являющийся делителем 60 https://stackru.com/questions/13274071/kak-nastroit-cron-dlya-zapuska-moego-skripta-kazhdyie-40-minut-25-minut


1.3 Комманда
В общем случае комманда, которую будет запускать крон, выглядит так
cd /[full path to project]/flalert-main && /[full path to project]/flalert-main/venv/bin/python3 main.py [parser_name] [time_span]
[full path to project] - полныю путь до папки проекта
*не забудьте указать параметры запуска, если сканируете каждые 10 минут, нужно указавыть чтобы программа отправляла задачи за каждые 10 минут.

2 Создаём задачи
Открываем либо список заданий с помощью "crontab -e", либо файл (я создал crontab-jobs)
Добавлем в него задачу(и)
Сохраняем и закрываем. Если работаете через файл, не забудьте прописать "crontab filename", к примеру "crontab crontab-jobs"

3 Пример
*/20 * * * * * cd /root/flalert-main && /root/flalert-main/venv/bin/python3 main.py profi 20
Каждые 20 минут, заходим в папку с проектом, который находится в директории root и оттуда запускаем, с помощью питона из виртуальной среды нашу программу, она в свою очередь запустит парсер для profi.ru и отправит спарсенные задачи за последние 20 минут

## Добавление нового парсера
1. Добавляем файл в папку parsers
- В программе должна быь функция _parse(), принимающая на вход переменную self (так как далее она будет использоваться как метод класса Parser). Соответственно из функции можно использовать другие методы класса Parser, при необходимости (Пример. self.normalize_href(...))
- Функция должна возвращать словарь с найдеными задачами в такой форме
``` json
{'checked_date': True,  # Добавьте это, если передаваемые задачи не нужно проверять по времени публикации
1: {'task_link': 'https://freelance.habr.com/tasks/573142', 
    'description': 'По результатам выполнения работ по развитию Система должна вклю...',
    'name': 'Настроить автоматический запуск', 
    'price': None, 
    'rate': 5000, 
    'date_publised': '2023-11-24 04:28:00',
    'client_info': {'avatar': False, 
                    'username_link': None, 
                    'username_info': None, 
                    'created_acc': 'Зарегистрирован на сайте меньше месяца', 
                    'orders': None, 
                    'feedback': 0}, 
    'type': None, 
    'stack': ['python'], 
    'legacy': None}, 
2: {'task_name': и так далее
```

2. Добавляем новый elif в функцию getParserFunc в файле config.py
``` python
def getParserFunc(site: str):
    if site == 'profi':
        from parsers.profi import _parse
    elif site == 'freelance':
        from  parsers.freelance_ru_parser import _parse
    elif site == 'SHORTNAME': <<==============
        from  parsers.FILENAME import _parse <<==============
    ...
```
3. Можем вызывать наш парсер коммандой
```bash
$ python3 main.py SHORTNAME [timespan]
``` 

## Запуск парсинга заказов profi.ru
``` bash
$ python main.py profi
```
При запуске, если есть новый заказ на почте, присылает json файл с деталями заказа 

запуск скрипта каждые 10 мин cron

```bash
*/10 * * * * python3 /путь_к_скрипту/main.py profi
```

### настройка config.py для profi.ru

**mail_pass** пароль от аккаунта почты

**username** логин от аккаунта почты

**imap_server** домен имап сервера
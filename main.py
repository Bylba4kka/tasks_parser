from datetime import datetime, timedelta
import argparse
import requests
import logging
import config
import pytz
import types
import re
import json



logging.basicConfig(format='%(asctime)s %(levelname)s - %(message)s',
                    level=logging.INFO, filename='main.log')



class Parser():
    def __init__(self, sleep_time, diapason: int) -> None:
        self.sleep_time = sleep_time
        self.ready_orders_dict = {}
        self.diapason = diapason
        self.make_href = "<a href='{}'>{}</a>"

    def start(self) -> None:
        ready_dict = self._parse()
        json_result = Json_worker(ready_dict)
        json_result.check_caluclate_parser_time(self.diapason, self.sleep_time)

    
    def normalize_href(self, url: str) -> str:
        url = url.replace("www.", "")
        if 'http' in url:
            url_split = url.split('/')[2].split('.')
            last_index = -1
            if len(url_split) > 2:
                last_index = -(len(url_split) - 1)
            return '.'.join(url_split[:-last_index])
        else:
            url_split = url.split('/')[0].split('.')
            last_index = -1
            if len(url_split) > 2:
                last_index = -(len(url_split) - 1)
            return '.'.join(url_split[:last_index])
    
    
    def find_digit_in_string(self, text: str) -> int:
        """
        Поиск чисел в строке
        """
        digit = ""
        for t in text:
            if t.isdigit():
                digit += t
        return int(digit) if digit != "" else 0

    def find_all_url_in_text(self, description: str) -> None:
        """
        Поиск и замена ссылок в описаниии habr.com и freelance.ru
        """
        urls_in_text = re.findall(r"(https?://\S+)", description)
        for url in urls_in_text:
            description = description.replace(url, self.make_href.format(url, self.normalize_href(url)))
        return description

    def _parse(self) -> None:
        print('Если вы видите это сообщение, значит, вы не подключили нужный парсер')
        return {}

def caluculate_diapason(date_now, diapason: int) -> tuple:
    '''
    Вычисляем временной диапазон
    '''
    d_sec = date_now.second
    d_msec = date_now.microsecond
    start_time = date_now - timedelta(minutes=diapason, seconds=d_sec, microseconds=d_msec)
    end_time = start_time + timedelta(minutes=diapason)
    print('Диапазон', start_time, end_time)
    return start_time, end_time

def cleandict(d: dict) -> dict:
    if not isinstance(d, dict):
        return d
    return dict((k,cleandict(v)) for k,v in d.items() if v is not None)

def post(url, data, timeout: int = 35):
    try:
        json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        response = requests.post(url, data=json_data, timeout = timeout)
        logging.info(f'Сервер ответил {response} {response.text}')
    except TimeoutError:
        logging.error(f'Сервер не ответил за {timeout} секунд')
        response = None
    except BaseException as e:
        logging.error(namespace.site)
        logging.error(e)
        logging.critical(e, exc_info=True)
        logging.error(json_data)
        response = None
    if not response:
        logging.info(json_data)

class Json_worker:
    def __init__(self, ready_dict: dict) -> None:
        self.ready_dict = ready_dict

    def price_with_strings(self, string: str) -> int:
        price = ''.join(filter(str.isdigit, string))
        return int(price) if price != '' else None

    def years_with_strings(self, string) -> None:
        arr_cr_data = []
        if string is not None:
            if 'лет' in string:
                arr_cr_data = string.split('лет')
            elif 'год' in string:
                arr_cr_data = string.split('год')
        years = ''

        if arr_cr_data != []:
            for register in arr_cr_data[0]:
                if register in '0123456789':
                    years += register
        if years == '':
            years = '0'
        return years
    
    def send_post_request(self, data_time_valid: dict) -> None:
            payload = {'messages': []}
            dtv = data_time_valid
            for data in dtv:
                #IMPORTANT
                task_description = dtv[data]['description']
                task_link = dtv[data]['task_link']
                task_name = dtv[data]['name']

                #NOT IMPORTANT
                legacy = dtv[data].get('legacy')
                task_type = dtv[data].get('type')
                stack = dtv[data].get('stack')
                
                task_price = dtv[data].get('price')
                if task_price and type(task_price) != int:
                    task_price = self.price_with_strings(task_price.lower().split('руб')[0]) if 'руб' in task_price else None
                rate = dtv[data].get('rate')

                if dtv[data].get('client_info'):
                    client_created_acc = dtv[data]['client_info'].get('created_acc')
                    if client_created_acc:
                        client_created_acc = self.years_with_strings(client_created_acc)
                    isAvatar = dtv[data]['client_info'].get('avatar') == True
                    client_orders = dtv[data]['client_info']['orders']
                    client_info = dtv[data]['client_info']['username_info']
                    feedback = dtv[data]['client_info'].get('feedback')
                else:
                    client_created_acc = None
                    client_orders = None
                    client_info = None
                    feedback = None
                    isAvatar = None
                
                data = {'link': task_link, #полная ссылка с хтппс
                        'text': task_description, #"текст задания"
                        'name': task_name, #Заголовок задания
                        'budget': task_price, #деньги, без копеек
                        'rate': rate, #Стоимость часа
                        'type': task_type, #тип разработки согласно нашему словарю
                        'legacy': legacy, #доработка или разработка
                        'stack': stack, #стек согласно нашему словарю
                        'client_years': client_created_acc, #как давно зарегистрирован
                        'client_orders': client_orders, #сколько 
                        'client_likes': feedback, #сумма лайков и дизлайков заказчика
                        'client_foto': isAvatar, #есть ли фото заказчика
                        'client_info': client_info, #описание заказчика
                        }
                
                clean_data = cleandict(data)
                payload['messages'].append(clean_data)

            if len(payload['messages']) > 0:
                post(config.post_url, payload)

    def check_caluclate_parser_time(self, diaposon, sleep_time) -> None:
        if not self.ready_dict.get('checked_date'):
            zone = 'Europe/Moscow'
            moscow_timezone = pytz.timezone(zone)
            start_diaposon, end_diaposon = caluculate_diapason(sleep_time.astimezone(moscow_timezone), diaposon)
            data_time_valid = {}
            self.ready_dict.pop('checked_date', None)
            for d in self.ready_dict:
                date_published = datetime.strptime(self.ready_dict[d]['date_publised'], "%Y-%m-%d %H:%M:%S")
                if start_diaposon.timestamp() <= date_published.timestamp() < end_diaposon.timestamp():
                    data_time_valid[d]= self.ready_dict[d]
        else:
            self.ready_dict.pop('checked_date', None)
            data_time_valid = self.ready_dict
        self.send_post_request(data_time_valid)



def CreateArgsParser():
    args_parser = argparse.ArgumentParser()
    #Здесь по хорошему убрать default и nargs, чтобы без аргументов не запускалась
    args_parser.add_argument ('site', default='fl', nargs='?')
    args_parser.add_argument ('diapason', default='3000', nargs='?')
 
    return args_parser

def main(sleep_time, parse_func, diapason: int) -> None:
    site_parser = Parser(
        diapason=diapason,
        sleep_time=sleep_time
        )
    site_parser._parse = types.MethodType(parse_func, site_parser)
    site_parser.start()


if __name__ == '__main__':
    argsParser = CreateArgsParser()
    namespace = argsParser.parse_args()
    
    _parse = config.getParserFunc(namespace.site, logging)
    logging.info(f'Starting parser for site {namespace.site} for {namespace.diapason} minutes.')
    #requests.post(config.post_url, data={'start': namespace.site})
    
    sleep_time = datetime.now(pytz.utc)

    try:
        main(sleep_time, _parse, int(namespace.diapason))
    except Exception as e:
        print(e)
        logging.error(namespace.site)
        logging.error(e)
        logging.critical(e, exc_info=True)

import re
import imaplib
import email
import logging

import requests

from email.header import decode_header
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode

from config import mail_pass, username, imap_server

imap = imaplib.IMAP4_SSL(imap_server)
imap.login(username, mail_pass)


# Функция получения итоговой ссылки
def get_final_redirect(initial_url):

    headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.135 YaBrowser/21.6.2.855 Yowser/2.5 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        }

    try:
        response = requests.get(initial_url, allow_redirects=False, headers=headers)
        if response.status_code == 302:
            redirect_url = response.headers['Location']
            return strip_link(redirect_url)
        else:
            logging.error("Initial URL didn't redirect or redirected with unexpected status code.")
            return None
    except Exception as ex:
        logging.error(ex)
        return None


def strip_link(initial_link):

    # Разбираем URL
    parsed_url = urlparse(initial_link)
    query_params = parse_qs(parsed_url.query)

    # Оставляем только параметры 'o' и '_prr'
    filtered_params = {key: value for key, value in query_params.items() if key in ['o']}

    # Собираем новый URL без лишних параметров
    stripped_link = parsed_url._replace(query=urlencode(filtered_params, doseq=True)).geturl()

    return stripped_link


# Функция, которая возвращает письма с заказами
def get_mail():
    # Получение непросмотренных сообщений
    imap.select("INBOX")
    unseen_inbox = imap.search(None, 'UNSEEN')
    # print("unseen_inbox", unseen_inbox)

    full_email_data = []

    if unseen_inbox[0] == 'OK':
        unseen_messages = unseen_inbox[1][0].split()
        for uid in unseen_messages:
            res, msg = imap.fetch(uid, '(RFC822)')  #Для метода search по порядковому номеру письма

            msg1 = email.message_from_bytes(msg[0][1])

            for part in msg1.walk():
                if part.get_content_type() == 'text/html':
                    email_data = decode_header(part.get_payload(decode=True).decode())
                    full_email_data.append(email_data)
    else:
        print("Ошибка в получении списка непрочитанных сообщений")
    print(full_email_data)
    return full_email_data



def _parse(self):
    counter = 0
    ready_dict = {'checked_date': True}

    email_data = get_mail()  # Получаем список писем

    for message in email_data:
            ready_order = parse_task(message)  # Передаем номер заказа в функцию parse_task
            counter += 1
            ready_dict[counter] = ready_order

    return ready_dict

# Функция распаршивания уже самого html письма
def parse_task(email_message):
    print("_parser for profi was called")
    html_message = get_mail()
    # Если новых сообщений нет возвращем None
    if html_message is None:
        return {}

    soup = BeautifulSoup(email_message[0][0], 'html.parser')

    # Получение ссылки заказа
    try:
        link = soup.find('a', class_="em_btn")["href"]
    except:
        link = None

    # Получение названия заказа
    try:
        table = soup.find("table").get_text()
        table = re.sub(r'\s+', ' ', table)
        if re.search(r'Стоимость', table):
            name = re.search(r'^(.*?)(?=Стоимость)', table).group(0).strip()
        elif re.search(r'Цель', table):
            name = re.search(r'^(.*?)(?=Цель)', table).group(0).strip()
        else:
            name = None
    except Exception as ex:
        name = None
        logging.error(ex)

    # Получение текста заказа
    try:
        text_budget = soup.find('td', valign="top").get_text()
        text = re.search(r'Цель:(.*?)Район:', text_budget, re.DOTALL).group(1).strip()
    except Exception:
        text = None
        logging.error(ex)

    # Получение бюджета
    try:
        # находим данные с текстом и бюджетом заказа
        text_budget = soup.find('td', valign="top").get_text()
        text_budget = re.sub(r'\s+', ' ', text_budget)
        # получаем только бюджет, но не цифру
        budget_to_goal = re.search(r'^(.*?)Цель:', text_budget)
        if budget_to_goal:
            budget_to_goal = budget_to_goal.group(1)
            # убиираем все пробелы
            numbers = budget_to_goal.replace(" ", "")
            # Ищем все цифры
            numbers = re.findall(r'\d+', budget_to_goal)
            # Переобразуем их в int
            numbers = [int(num) for num in numbers]
            # Получаем цену, если там от и до и получаем цену до
            max_number = max(numbers)
        budget = max_number
    except Exception as ex:
        budget = None
        logging.error(ex)

    ready_order = {
                    'name': name,
                    'task_link': get_final_redirect(link),
                    'description': text,
                    'price': budget,
                }

    return ready_order


print(get_final_redirect("https://b.profi.ru/1qcgSPIFZFl8AgQu"))
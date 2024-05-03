from bs4 import BeautifulSoup
from dateutil.parser import parse as dateutil_parse
import requests
import asyncio
import re

trancelate = {'января': 'january', 'февраля': 'february', 'марта': 'march', 'апреля': 'april', 'мая': 'may', 'июня': 'june', 'июля': 'july', 'августа': 'august', 'сентября': 'september', 'октября': 'october', 'ноября': 'november', 'декабря': 'december'}


class Mainloop:
    def __init__(self):
        self.mainloop = asyncio.get_event_loop()

    def start_mainloop(self, coroutine) -> None:
        try:
            self.mainloop.run_until_complete(coroutine)
        except KeyboardInterrupt:
            self.mainloop.close()

class Pagination(Mainloop):
    def __init__(self, url: str, filter_url: str = '', pagination: bool=False) -> None:
        self.url = url
        self.filter_url = filter_url
        self.pagination = pagination
        self.pagination_pages = []

        super().__init__()
        self.start_mainloop(self._get_pagination_pages(self._get_page_count(self.url) + 1))

    def _get_page_count(self, url: str) -> int:
        html_data = get_response(url, self.filter_url).text

        soup = BeautifulSoup(html_data, 'html.parser')
        pagination_div = soup.find_all('div', class_='pagination')

        if not pagination_div:
            html_data = get_response(f'{url}?page=1', self.filter_url).text
            soup = BeautifulSoup(html_data, 'html.parser')
            pagination_div = soup.find_all('ul', class_='content-list content-list_tasks')
            
            assert pagination_div, 'page is empty'
            return 1

        pagination_text = BeautifulSoup(pagination_div[0].text, 'html.parser')

        links = pagination_text.text.split(' ')

        for i in links:
            if i.isdigit():
                max_pag_number = int(i)
                
        if self.pagination:
            return max_pag_number
        else:
            return 1

    async def _get_list_futures(self, url: str, page_count: int) -> None:
        return [self.mainloop.run_in_executor(None, get_response, f'{url}?page={i}', self.filter_url) for i in range(1, page_count)]

    async def _get_pagination_pages(self, page_count: int) -> list:
        for page in await self._get_list_futures(self.url, page_count):
            asyncio.ensure_future(page)
            self.pagination_pages.append(await page)
        return self.pagination_pages


class Decorators:
    @staticmethod
    def check_http(func):
        def wrapper(url: str):
            assert any((url.startswith('http://'), url.startswith('https://'))), 'invalid url address (url must statswich on "http://" or "https://")'
            return func(url)
        return wrapper

decs = Decorators()

class Validation:
    def __init__(self, url: str) -> None:
        self.url = url

        self.check_valid_url(self.url)

    @staticmethod
    @decs.check_http
    def check_valid_url(url: str) -> None:
        assert url.endswith('freelance.habr.com/tasks'), 'parser supports only website freelance.habr.com'



def gen_filename_by_url(url: str, filetype: str) -> str:
    filename = url.replace('http://', '').replace('https://', '').replace('/', '_') + f'.{filetype}'
    return filename

def get_response(url: str, filter_url: str = None) -> requests.Response:
    if filter_url:
        if '?' in url:
            url += f'&{filter_url}'
        else:
            url += f'?{filter_url}'

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.135 YaBrowser/21.6.2.855 Yowser/2.5 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    }
    try:
        response = requests.get(url, headers=headers)
    except Exception:
        print('page is not found')
        exit()

    return response




def _parse(self):
    counter = 0
    ready_dict = {'checked_date': False}
    default_avatar = 'https://freelance.habr.com/assets/default/users/avatar_r100-510ec240a9384f321c7075c46962f4fad15dd58cd22cd41d7f1ca9b2e1732c00.png'
    url = 'https://freelance.habr.com/tasks'
    filter_and_type = {'development_bots': None,
                        'development_frontend': None,
                        'design_landings': "webdesign",
                        'development_backend': None,
                        'development_voice_interfaces': None,
                        'design_sites': "webdesign",
                        'development_scripts': None,
                        'development_prototyping': None,
                        'development_android': "mobile",
                        'development_other': None,
                        'development_games': None,
                        'development_all_inclusive': None,
                        'development_1c_dev': None,
                        'development_desktop': None,
                        'development_ios': "mobile",
                        'design_mobile': "webdesign"}
    Validation(url)

    url_client = 'https://freelance.habr.com'
    task_types = set(filter_and_type.values())
    for task_type in task_types:
        category = 'categories='+','.join([filter_cat for filter_cat in filter_and_type.keys() if filter_and_type[filter_cat]==task_type])
        pag = Pagination(url, category, pagination=False)
        for resp in pag.pagination_pages:
            temp_parser = BeautifulSoup(resp.text, 'html.parser')
            orders = temp_parser.find_all('li', class_=['content-list__item', 'content-list__item content-list__item_marked'])

            for order in orders:
                ready_order = parse_task(self, filter_and_type, url_client, task_type, default_avatar, order)
                counter += 1
                ready_dict[counter] = ready_order
    return ready_dict

def parse_task(self, filter_and_type, url_client, task_type, default_avatar, order):
    technologies = list(map(lambda t: t.text, order.findAll('a', class_='tags__item_link')))
    stack = make_stack(technologies)
    date_published_str = order.findAll('span', class_='params__published-at icon_task_publish_at')[0].text
    description = []
    task = order.findAll('a')[0].text
    task_link = url_client + order.findAll('a')[0]['href']
    habr_price = order.findAll('span', class_=['count', 'negotiated_price'])[0].text
    if 'час' in habr_price:
        rate = int(''.join(filter(str.isdigit, habr_price)))
        price = None
    else:
        rate = None
        price = 'Бюджет: ' + habr_price.replace('договорная', '?') + ' Срок: ?'
                
    task_page  =  BeautifulSoup(get_response(task_link).text, 'html.parser')
    description = task_page.find_all('div', class_='task__description')[0].text.replace('\n', ' ') if task_page.find_all('div', class_='task__description') else ''
    meta_tags = ' '.join(task_page.find_all('div', class_='task__meta')[0].text.replace('\n', ' ').split())
    avatar = url_client + task_page.find('img', class_='avatario')['src'] if 'https' not in task_page.find('img', class_='avatario')['src'] else task_page.find('img', class_='avatario')['src']
    true_avatar = False if avatar == default_avatar else True
    #username = task_page.find_all('div', class_='fullname')[0]
    #username_link = url_client + username.find_all('a')[0]['href']
    username_info = task_page.find_all('div', class_='specialization')[0].text \
                                    + task_page.find_all('div', class_='meta')[0].text
    #verification = True if task_page.find('span', 'verified') else False
    static_emploer = task_page.find_all('div', 'row')
    active_emploer = static_emploer[1].find('div', class_='value').text
    find_freelance = static_emploer[2].find('div', class_='value').text
    arbitage_emploer = static_emploer[3].find('div', class_='value').text.replace(' ', '').replace('\n', '')
    created_acc = task_page.find_all('div', class_='divider row')[-1].text.replace('\n', ' ') if task_page.find_all('div', class_='divider row') else "Нет информации о регистрации"
    feedback = int(static_emploer[4].find('div', class_='value').text.split('/')[0]) - int(static_emploer[4].find('div', class_='value').text.split('/')[1])
                
    #file_add =  True if task_page.find_all('dl', class_='user-params') else False
    date = meta_tags.split('•')[0]
    month = meta_tags.split('•')[0].split(' ')[1]
    date = date.replace(month, trancelate[month])
    date_published = dateutil_parse(date)
                
    for a_ in task_page.find('div', class_='task__description').find_all('a', href=True):
        if len(a_.contents)>0:
            url_content = a_.contents[0].text
        else:
            url_content = a_['href']
        description = description.replace(url_content, self.make_href.format(a_['href'], self.normalize_href(a_['href'])))
    
    ready_order = {
                    'name': task,
                    'task_link': task_link,
                    'description': self.find_all_url_in_text(description),
                    'price': price,
                    'rate': rate,
                    'type': task_type,
                    'stack': stack,
                    'date_publised': str(date_published),
                    'date_published_str': date_published_str,
                    #'file_add': file_add,
                    'client_info': {
                        #'client_name': username.text.replace('\n', ''),
                        'avatar': true_avatar,
                        #'username_link': username_link,
                        'username_info': username_info.replace('\n', ' ') if len(username_info) > 1 else None,
                        'created_acc': created_acc,
                        #'verification': verification,
                        'orders': int(active_emploer) + int(find_freelance.replace('\n', '')) + int(arbitage_emploer),
                        'feedback': feedback
                    }
                }
    return ready_order

def make_stack(technologies):
    if len(technologies) > 5:
        stack = None
    else:
        stack = []
        for tech in technologies:
            if not bool(re.search('[а-яА-Я .]', tech)):
                if tech.lower() == 'c++':
                    tech = 'cPlus'
                elif tech.lower() == 'c#':
                    tech = 'cSharp'
                elif tech.endswith('.js'):
                    tech = tech[:-3]
                stack.append(tech)
        stack = stack if len(stack) > 0 else None
    return stack


post_url = 'https://228.requestcatcher.com/'

# для profi.ru
mail_pass = "******"
username = "*****@rambler.ru"
imap_server = "imap.rambler.ru"

def getParserFunc(site: str, logging):
    if site == 'fl':
        from parsers.profi import _parse
        return _parse
    elif site == 'habr':
        from parsers.habr import _parse
        return _parse
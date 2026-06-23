import requests
from re import search


class Api():
    def __init__(self, channel, post) -> None:
        self.url = 'https://t.me/'
        self.channel = channel
        self.post = post
        
        # Instance variables (tiap user punya sendiri)
        self.real_views = 0
        self.proxy_errors = 0
        self.token_errors = 0
        self.success_views = 0

    def views(self):
        """Update real_views dari Telegram"""
        try:
            telegram_request = requests.get(
                f'{self.url}{self.channel}/{self.post}', 
                params={'embed': '1', 'mode': 'tme'},
                headers={
                    'referer': f'{self.url}{self.channel}/{self.post}', 
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
                },
                timeout=15
            )
            result = search(
                '<span class="tgme_widget_message_views">([^<]+)', 
                telegram_request.text
            )
            if result:
                self.real_views = result.group(1)
        except Exception:
            pass  # biarkan views tetap seperti sebelumnya

    def send_view(self, proxy, proxy_type):
        """Kirim 1 view via proxy"""
        try:
            session = requests.session()
            response = session.get(
                f'{self.url}{self.channel}/{self.post}', 
                params={'embed': '1', 'mode': 'tme'},
                headers={
                    'referer': f'{self.url}{self.channel}/{self.post}', 
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
                },
                proxies={
                    'http': f'{proxy_type}://{proxy}', 
                    'https': f'{proxy_type}://{proxy}'
                },
                timeout=15
            )   
            
            cookies_dict = session.cookies.get_dict()
            session.get(
                'https://t.me/v/', 
                params={'views': str(search('data-view="([^"]+)', response.text).group(1))}, 
                cookies={
                    'stel_dt': '-240', 
                    'stel_web_auth': 'https%3A%2F%2Fweb.telegram.org%2Fz%2F',
                    'stel_ssid': cookies_dict.get('stel_ssid', None), 
                    'stel_on': cookies_dict.get('stel_on', None)
                },
                headers={
                    'referer': f'https://t.me/{self.channel}/{self.post}?embed=1&mode=tme',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36', 
                    'x-requested-with': 'XMLHttpRequest'
                },
                proxies={
                    'http': f'{proxy_type}://{proxy}', 
                    'https': f'{proxy_type}://{proxy}'
                },
                timeout=15
            )
            
            # ✅ Sukses
            self.success_views += 1
            
        except AttributeError:
            self.token_errors += 1
        except requests.exceptions.RequestException:
            self.proxy_errors += 1

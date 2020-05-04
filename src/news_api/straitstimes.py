import requests
from bs4 import BeautifulSoup
from bs4 import element

class StraitsTimesAgent(object):

    def __init__(self, url):
        self.url = url
        self.res = None

    def get_content(self):
        if not self.res:
            self.res = requests.get(self.url)

        soup = BeautifulSoup(self.res.text, features="lxml")
        texts = soup.select(".odd.field-item > p")

        result_text = ""

        for text in texts:
            if type(text.contents[0]) is element.NavigableString:
                result_text = result_text + text.get_text() + "\n"

        return result_text

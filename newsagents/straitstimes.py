import requests
from bs4 import BeautifulSoup
from bs4 import element

class StraitsTimesAgent(object):

    def __init__(self, url):
        self.url = url
        self.res = requests.get(url)

    def get_author(self):
        soup = BeautifulSoup(self.res.text, features="lxml")
        author = soup.select_one(".author-field.author-name")
        
        if author:
            return author.get_text()
        else:
            return ""

    def get_content(self):
        soup = BeautifulSoup(self.res.text, features="lxml")
        texts = soup.select(".odd.field-item > p")

        result_text = ""

        for text in texts:
            if type(text.contents[0]) is element.NavigableString:
                result_text = result_text + text.get_text() + "\n"
        
        return result_text


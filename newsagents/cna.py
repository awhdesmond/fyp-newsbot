# -*- coding: utf-8 -*-

import requests
import random

from bs4 import BeautifulSoup
from bs4 import element

class CNAAgent(object):

    def __init__(self, url):
        self.url = url
        
        headers = {
            'referer': "https://www.channelnewsasia.com/",
            'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        }

        self.res = requests.get(url, headers=headers)

    def get_author(self):
        soup = BeautifulSoup(self.res.text, features="lxml")
        author = soup.select_one(".article__author-title")
        
        if author:
            return " ".join(author.get_text().split(" ")[1:]).strip()
        else:
            return ""

    def get_content(self):
        soup = BeautifulSoup(self.res.text, features="lxml")
        texts = soup.select(".c-rte--article p")

        result_text = ""

        for text in texts:
            if "©" not in text.get_text().encode('utf-8'):
                result_text = result_text + text.get_text() + "\n"
        
        return result_text
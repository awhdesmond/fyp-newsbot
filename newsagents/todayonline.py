# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from bs4 import element

class TodayOnlineAgent(object):

    def __init__(self, url):        
        res = requests.get(url)
        soup = BeautifulSoup(res.text, features="lxml")
        meta_id = soup.find("meta", {"name":"cXenseParse:recs:articleid"})["content"]
        
        self.url = "https://www.todayonline.com/api/v3/article/" + meta_id
        self.res = requests.get(self.url)
        
    def get_author(self):
        if len(self.res.json()["node"]["author"]) > 0:
            return self.res.json()["node"]["author"][0]["name"]
        else:
            return ""

    def get_content(self):
        soup = BeautifulSoup(self.res.json()["node"]["body"], features="lxml")
        texts = soup.select("p")

        result_text = ""
        for text in texts:
            result_text = result_text + text.get_text() + "\n"
        
        return result_text
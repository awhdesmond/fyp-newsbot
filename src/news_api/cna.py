
import requests
from bs4 import BeautifulSoup

from common import agents


class CNAAgent:
    def __init__(self, url: str):
        self.url = url
        self.res = None

    def get_content(self):
        if not self.res:
            headers = {
                "referer": "https://www.channelnewsasia.com/",
                "user-agent": agents.HTTP_USER_AGENT
            }
            self.res = requests.get(self.url, headers=headers)

        soup = BeautifulSoup(self.res.text, features="lxml")
        texts = soup.select(".c-rte--article p")

        result_text = "\n".join([t.get_text() for t in texts if "©" not in t.get_text()])
        return result_text

from pydantic import BaseModel


class Article(BaseModel):
    source: str = ""
    url: str = ""
    imageurl: str = ""
    title: str = ""
    author: str = ""
    publishedDate: str = ""
    content: str = ""

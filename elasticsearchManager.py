from elasticsearch import Elasticsearch

ELASTICSEARCH_HOST = 'http://128.199.101.98:9200'

class ElasticsearchManager(object):

    def __init__(self):
        self.es = Elasticsearch([ELASTICSEARCH_HOST])

    def indexDocument(self, index, docType, doc, id=None):
        if id is None:
            return self.es.index(index=index, doc_type=docType, body=doc)
        else:
            return self.es.index(index=index, doc_type=docType, body=doc, id=id)

    
    def indexCount(self, index, docType):
        searchBody = {
            "query": {
                "match_all": {}
            }
        }
        return self.es.count(index=index, doc_type=docType, body=searchBody)["count"]

    # TODO: improve this
    def searchIndex(self, index, docType, searchBody, size=None):
        return self.es.search(index=index, doc_type=docType, body=searchBody, size=size)

    def deleteByQuery(self, index, docType, queryBody):
        return self.es.delete_by_query(index=index, doc_type=docType, body=queryBody)
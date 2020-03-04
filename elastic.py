from elasticsearch import Elasticsearch

class ElasticsearchManager:
    def __init__(self, host="localhost:9200"):
        self.es = Elasticsearch([host])
        
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

    def bulk(self, index, docType, body):
        return self.es.bulk(index=index, doc_type=docType, body=body, request_timeout=10000)

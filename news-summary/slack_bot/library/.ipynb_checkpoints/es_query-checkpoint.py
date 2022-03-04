from elasticsearch import Elasticsearch
import os
def request_data(u_index):
    client = Elasticsearch(
        os.environ['ES_ENDPOINT'],
        api_key=("I1dGVX8BwL4ThBFcQbLA", "-yvqiJncSuS_ny9cvQSHpw")
    )
                          
    result = client.search(
        index= u_index,  
        size=10000,
        query={
                'match_all':{}
            }
        
    )
    return result

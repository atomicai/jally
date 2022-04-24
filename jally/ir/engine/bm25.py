import json
import logging
import string
from typing import Dict, Generator, List, Optional, Union

from more_itertools import chunked
from nlp.ir.document_store.base.store import Document
from nlp.ir.document_store.elastic.store import ElasticDocStore
from nlp.ir.engine import base as base_engine

logger = logging.getLogger(__name__)


class BM25Retriever(base_engine.IR):
    def __init__(self, store: ElasticDocStore, top_k: Optional[int] = 10):
        super().__init__(store, query_processor=None, query_model=None)
        self.top_k = top_k

    def retrieve_top_k(
        self,
        query: Union[str, List[Dict]],
        filters: Optional[Dict[str, List[Dict]]] = None,
        top_k: int = None,
        batch_size: int = 10_000,
        custom_query: Optional[str] = None,
        index: Optional[str] = None,
    ) -> List[Document]:
        if self.store.index is None:
            index = self.store.index
        top_k = top_k or self.top_k
        if isinstance(query, str):
            query = [{"query": query}]

        # Naive retrieval without BM25, only filtering
        if query is None:
            body = {"query": {"bool": {"must": {"match_all": {}}}}}
            if filters:
                filter_clause = []
                for key, values in filters.items():
                    filter_clause.append({"terms": {key: values}})
                body["query"]["bool"]["filter"] = filter_clause

        # Retrieval via custom query
        elif custom_query:  # substitute placeholder for query and filters for the custom_query template string
            template = string.Template(custom_query)
            # replace all "${query}" placeholder(s) with query
            substitutions = {"query": f'"{query}"'}
            # For each filter we got passed, we'll try to find & replace the corresponding placeholder in the template
            # Example: filters={"years":[2018]} => replaces {$years} in custom_query with '[2018]'
            if filters:
                for key, values in filters.items():
                    values_str = json.dumps(values)
                    substitutions[key] = values_str
            custom_query_json = template.substitute(**substitutions)
            body = json.loads(custom_query_json)
            # add top_k
            body["size"] = str(top_k)

        # Default Retrieval via BM25 using the user query on `self.search_fields`
        else:
            for i, batch in enumerate(chunked(query, batch_size)):
                response = []
                for j, q in enumerate(batch):
                    body = {
                        "size": str(top_k),
                        "query": {
                            "bool": {
                                "should": [
                                    {
                                        "multi_match": {
                                            "query": q["query"],
                                            "type": "most_fields",
                                            "fields": self.store.search_fields,
                                        }
                                    }
                                ]
                            }
                        },
                    }

                    if filters:
                        filter_clause = []
                        for key, values in filters.items():
                            if type(values) != list:
                                raise ValueError(
                                    f'Wrong filter format for key "{key}": Please provide a list of allowed values for each key. '
                                    'Example: {"name": ["some", "more"], "category": ["only_one"]} '
                                )
                            filter_clause.append({"terms": {key: values}})
                        body["query"]["bool"]["filter"] = filter_clause

                    if self.store.excluded_meta_data:
                        body["_source"] = {"excludes": self.store.excluded_meta_data}

                    logger.debug(f"Retriever query: {body}")
                    result = self.store.client.search(index=index, body=body)["hits"]["hits"]

                    documents = [
                        self.store._convert_es_hit_to_document(hit, return_embedding=self.store.return_embedding)
                        for hit in result
                    ]
                    response.append(documents)

                yield response

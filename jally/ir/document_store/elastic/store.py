import json
import logging
import time
from copy import deepcopy
from string import Template
from typing import Any, Dict, Generator, List, Optional, Union

import numpy as np
import torch
import torch.nn as nn
from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch.exceptions import RequestError
from elasticsearch.helpers import bulk, scan
from jally.formatting.ir import tool
from jally.ir.document_store.base import BaseDocStore, Document
from scipy.special import expit
from tqdm.auto import tqdm

logger = logging.getLogger(__name__)


class ElasticDocStore(BaseDocStore):

    """
    Most of the code is taken from
    https://github.com/deepset-ai/haystack/blob/master/haystack/document_stores/elasticsearch.py
    However many params seems redundant and some calls are not async by default which may cause unexpected blocking
    E.g. when deleting doc(s) `wait_for_completion`...
    """

    def __init__(
        self,
        host: Union[str, List[str]] = "localhost",
        port: Union[int, List[int]] = 9200,
        username: str = "",
        password: str = "",
        index: str = "document",
        label_index: str = "label",
        search_fields: Union[str, list] = "text",
        text_field: str = "text",
        name_field: str = "name",
        embedding_field: str = "embedding",
        embedding_dim: int = 768,
        custom_mapping: Optional[dict] = None,
        excluded_meta_data: Optional[list] = None,
        analyzer: str = "standard",
        scheme: str = "http",
        ca_certs: Optional[str] = None,
        verify_certs: bool = True,
        create_index: bool = True,
        refresh_type: str = "wait_for",
        similarity="dot_product",
        timeout=30,
        request_timeout=300,
        return_embedding: bool = False,
        index_type: str = "flat",
        scroll: str = "1d",
    ):

        if type(search_fields) == str:
            search_fields = [search_fields]

        self.search_fields = search_fields
        self.content_field = text_field
        self.name_field = name_field
        self.embedding_field = embedding_field
        self.embedding_dim = embedding_dim
        self.excluded_meta_data = excluded_meta_data
        self.analyzer = analyzer
        self.return_embedding = return_embedding

        self.custom_mapping = custom_mapping
        self.index = index
        self.label_index = label_index
        self.scroll = scroll

        assert similarity in ["cosine", "dot_product", "l2"]
        self.similarity = similarity
        assert index_type in ["flat", "hnsw"]

        self.request_timeout = request_timeout
        self.refresh_type = refresh_type

        self.client = self._init_elastic_client(
            host=host,
            port=port,
            username=username,
            password=password,
            scheme=scheme,
            ca_certs=ca_certs,
            verify_certs=verify_certs,
            timeout=timeout,
        )

        if create_index:
            self._create_document_index(index)
        self.refresh_type = refresh_type

    def write_documents(
        self,
        documents: Union[List[dict], List[Document]],
        index: Optional[str] = None,
        batch_size: int = 10_000,
        duplicate_documents: Optional[str] = None,
    ):
        if index and not self.client.indices.exists(index=index):
            self._create_document_index(index)

        if index is None:
            index = self.index

        field_map = self._create_document_field_map()
        document_objects = [Document.from_dict(d, field_map=field_map) if isinstance(d, dict) else d for d in documents]

        docs_to_index = []
        for doc in document_objects:
            _doc = {
                "_op_type": "index",
                "_index": index,
                **doc.to_dict(field_map=self._create_document_field_map()),
            }

            # cast embedding type as ES cannot deal with np.array
            if _doc[self.embedding_field] is not None:
                if type(_doc[self.embedding_field]) == np.ndarray:
                    _doc[self.embedding_field] = _doc[self.embedding_field].tolist()

            # rename id for elastic
            _doc["_id"] = str(_doc.pop("id"))

            # don't index query score and empty fields
            _ = _doc.pop("score", None)

            _doc = {k: v for k, v in _doc.items() if v is not None}

            # In order to have a flat structure in elastic + similar behaviour to the other DocumentStores,
            # we "unnest" all value within "meta"
            if "meta" in _doc.keys():
                for k, v in _doc["meta"].items():
                    _doc[k] = v
                _doc.pop("meta")
            docs_to_index.append(_doc)

            # Pass batch_size number of documents to bulk
            if len(docs_to_index) % batch_size == 0:
                bulk(
                    self.client,
                    docs_to_index,
                    request_timeout=self.request_timeout,
                    refresh=self.refresh_type,
                )
                docs_to_index = []

        # Push the remainder as well
        if len(docs_to_index) > 0:
            bulk(
                self.client,
                docs_to_index,
                request_timeout=self.request_timeout,
                refresh=self.refresh_type,
            )

    def get_all_documents(
        self,
        index: Optional[str] = None,
        filters: Optional[Dict[str, List[str]]] = None,
        return_embedding: Optional[bool] = None,
        batch_size: Optional[int] = 10_000,
    ):
        """
        Get documents from the document store.
        :param index: Name of the index to get the documents from. If None, the
                        DocumentStore's default index (self.index) will be used.
        :param filters: Optional filters to narrow down the documents to return.
                                Example: {"name": ["some", "more"], "category": ["only_one"]}
        :param return_embedding: Whether to return the document embeddings.
        :param batch_size: When working with large number of documents, batching can help reduce memory footprint.
        """
        result = self.get_all_documents_generator(
            index=index, filters=filters, return_embedding=return_embedding, batch_size=batch_size
        )
        documents = list(result)
        return documents

    def update_document_meta(self, _id: str, meta: Dict[str, str]):
        """
        Update the metadata dictionary of a document by specifying its string id
        """
        body = {"doc": meta}
        self.client.update(index=self.index, id=_id, body=body, refresh=self.refresh_type)

    def get_all_documents_generator(
        self,
        index: Optional[str] = None,
        filters: Optional[Dict[str, List[str]]] = None,
        return_embedding: Optional[bool] = None,
        batch_size: int = 10_000,
    ) -> Generator[Document, None, None]:
        """
        Get documents from the document store. Under-the-hood, documents are fetched in batches from the
        document store and yielded as individual documents. This method can be used to iteratively process
        a large number of documents without having to load all documents in memory.
        :param index: Name of the index to get the documents from. If None, the
                      DocumentStore's default index (self.index) will be used.
        :param filters: Optional filters to narrow down the documents to return.
                        Example: {"name": ["some", "more"], "category": ["only_one"]}
        :param return_embedding: Whether to return the document embeddings.
        :param batch_size: When working with large number of documents, batching can help reduce memory footprint.
        """

        if index is None:
            index = self.index

        if return_embedding is None:
            return_embedding = self.return_embedding

        result = self._get_all_documents_in_index(index=index, filters=filters, batch_size=batch_size)
        for hit in result:
            document = self._convert_es_hit_to_document(hit, return_embedding=return_embedding)
            yield document

    def get_document_count(
        self,
        filters: Optional[Dict[str, List[str]]] = None,
        index: Optional[str] = None,
        only_documents_without_embedding: Optional[bool] = False,
    ) -> int:
        index = index or self.index

        body: dict = {"query": {"bool": {}}}
        if only_documents_without_embedding:
            body['query']['bool']['must_not'] = [{"exists": {"field": self.embedding_field}}]

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

        result = self.client.count(index=index, body=body)
        count = result["count"]
        return count

    def get_documents_by_id(self, ids, index: Optional[str] = None, **kwargs) -> List[Document]:
        index = self.index if index is None else index
        query = {"query": {"ids": {"values": ids}}}
        response = self.client.search(index=index, body=query)["hits"]["hits"]
        documents = [self._convert_es_hit_to_document(hit, return_embedding=self.return_embedding) for hit in response]
        return documents

    def query_by_embedding(
        self,
        query_emb: np.ndarray,
        filters: Optional[Dict[str, List[str]]] = None,
        top_k: int = 10,
        index: Optional[str] = None,
        return_embedding: Optional[bool] = None,
    ) -> List[Document]:
        """
        Find the document that is most similar to the provided `query_emb` by using a vector similarity metric.
        :param query_emb: Embedding of the query (e.g. gathered from DPR)
        :param filters: Optional filters to narrow down the search space.
                        Example: {"name": ["elon_musk"], "category": ["twitter"]}
        :param top_k: How many documents to return
        :param index: Index name for storing the docs and metadata
        :param return_embedding: To return document embedding
        :return:
        """
        index = self.index if index is None else index
        return_embedding = self.return_embedding if return_embedding is None else return_embedding

        body = {
            "size": top_k,
            "query": tool.elastic_query_api(self.similarity, query_emb, embedding_field=self.embedding_field),
        }

        if filters:
            filter_clause = []
            for k, v in filters.items():
                filter_clause.append({"terms": {k: v}})

            body["query"]["script_score"]["query"] = {"bool": {"filter": filter_clause}}

        # Finally make a request. TODO: time it up
        try:
            response = self.client.search(index=index, body=body, request_timeout=self.request_timeout)["hits"]["hits"]
        except RequestError as e:
            if e.error == "search_phase_execution_exception":
                error_message: str = (
                    "search_phase_execution_exception: Likely some of your stored documents don't have embeddings."
                    " Run the document store's update_embeddings() method."
                )
                raise RequestError(e.status_code, error_message, e.info)
            else:
                raise e

        documents = [
            self._convert_es_hit_to_document(hit, adapt_score_for_embedding=True, return_embedding=return_embedding)
            for hit in response
        ]

        return documents

    def describe(self, index=None):
        """Similar to pandas.describe(...)
        Returns stats of the documents in the store such as distribution of the characters, mean, max, etc...
        """
        index = self.index if index is None else index
        docs = self.get_all_documents(index)
        cp = [len(d.text) for d in docs]
        stats = {
            "count": len(docs),
            "chars_mean": np.mean(cp),
            "chars_max": max(cp) if len(cp) > 0 else 0,
            "chars_min": min(cp) if len(cp) > 0 else 0,
            "chars_median": np.median(cp) if len(cp) > 0 else 0,
        }
        return stats

    def update_embeddings(
        self,
        retriever: nn.Module,
        index: Optional[str] = None,
        filters: Optional[Dict[str, List[str]]] = None,
        update_existing_embeddings: bool = True,
        batch_size=10_000,
    ):
        """
        Updates the embeddings in the the document store using the encoding model specified in the retriever.
        This can be useful if want to add or change the embeddings for your documents (e.g. after changing the retriever config).
        :param retriever: Retriever to use to update the embeddings.
        :param index: Index name to update
        :param update_existing_embeddings: Whether to update existing embeddings of the documents. If set to False,
                                           only documents without embeddings are processed. This mode can be used for
                                           incremental updating of embeddings, wherein, only newly indexed documents
                                           get processed.
        :param filters: Optional filters to narrow down the documents for which embeddings are to be updated.
                        Example: {"name": ["elon_musk"], "category": ["tweeter"]}
        :param batch_size: When working with large number of documents, batching can help reduce memory footprint.
        :return: None
        """
        index = self.index if index is None else index
        if self.refresh_type == "false":
            self.client.indices.refresh(index=index)

        if update_existing_embeddings:
            document_count = self.get_document_count(index=index)
            logger.info(f"Updating embeddings for all {document_count} docs ...")
        else:
            document_count = self.get_document_count(index=index, filters=filters, only_documents_without_embedding=True)
            logger.info(f"Updating embeddings for {document_count} docs without embeddings ...")

        response = self._get_all_documents_in_index(
            index=index,
            filters=filters,
            batch_size=batch_size,
            only_documents_without_embedding=not update_existing_embeddings,
        )

        with tqdm(total=document_count, position=0, unit="Docs", desc="Update embeddings") as pb:
            for chunk in tool.get_batches_from_generator(response, batch_size):
                document_batch = [self._convert_es_hit_to_document(hit, return_embedding=False) for hit in chunk]
                # TODO: Replace fake generating with nn.Module
                # embeddings = retriever.embed_passages(document_batch)  # type: ignore
                embeddings = torch.rand(len(document_batch), self.embedding_dim)
                assert len(document_batch) == len(embeddings)

                doc_updates = []
                for doc, emb in zip(document_batch, embeddings):
                    update = {
                        "_op_type": "update",
                        "_index": index,
                        "_id": doc.id,
                        "doc": {self.embedding_field: emb.tolist()},
                    }
                    doc_updates.append(update)

                bulk(
                    self.client,
                    doc_updates,
                    request_timeout=self.request_timeout,
                    refresh=self.request_timeout,
                )
                pb.update(batch_size)

    def delete_documents(
        self,
        index: Optional[str] = None,
        ids: Optional[List[str]] = None,
        filters: Optional[Dict[str, List[str]]] = None,
    ):
        index = self.index if index is None else index
        query = {"query": {}}
        if filters:
            filter_clause = []
            for k, vs in filters.items():
                filter_clause.append({"terms": {k: vs}})
                query["query"]["bool"] = {"filter": filter_clause}

            if ids:
                query["query"]["bool"]["must"] = {"ids": {"values": ids}}

        elif ids:
            query["query"]["ids"] = {"values": ids}
        else:
            query["query"] = {"match_all": {}}
        # TODO: The call is blocking by default, therefore we pass `wait_for_completion=False`
        # Not sure: shall we pass the callback to be invoked as soon as all docs are deleted ?
        response = self.client.delete_by_query(index=index, body=query, ignore=[404], wait_for_completion=False)
        return response

    def _init_elastic_client(
        self,
        host: Union[str, List[str]],
        port: Union[int, List[int]],
        username: str,
        password: str,
        scheme: str,
        ca_certs: Optional[str],
        verify_certs: bool,
        timeout: int,
    ) -> Elasticsearch:

        hosts = self._prepare_hosts(host, port)
        client = Elasticsearch(
            hosts=hosts,
            scheme=scheme,
            ca_certs=ca_certs,
            verify_certs=verify_certs,
            timeout=timeout,
        )
        return client

    def _prepare_hosts(self, host, port):
        # Create list of host(s) + port(s) to allow direct client connections to multiple elasticsearch nodes
        if isinstance(host, list):
            if isinstance(port, list):
                if not len(port) == len(host):
                    raise ValueError("Length of list `host` must match length of list `port`")
                hosts = [{"host": h, "port": p} for h, p in zip(host, port)]
            else:
                hosts = [{"host": h, "port": port} for h in host]
        else:
            hosts = [{"host": host, "port": port}]
        return hosts

    # TODO: Add flexibility to define other non-meta and meta fields expected by the Document class
    def _create_document_field_map(self) -> Dict:
        return {self.content_field: "text", self.embedding_field: "embedding"}

    def _create_document_index(self, index_name: str):
        """
        Create a new index for storing documents. In case if an index with the name already exists, it ensures that
        the embedding_field is present.
        """
        if self.client.indices.exists(index=index_name):
            if self.embedding_field:
                mapping = self.client.indices.get(index_name)[index_name]["mappings"]
                if (
                    self.embedding_field in mapping["properties"]
                    and mapping["properties"][self.embedding_field]["type"] != "dense_vector"
                ):
                    raise Exception(
                        f"The '{index_name}' index in Elasticsearch already has a field called '{self.embedding_field}'"
                        f" with the type '{mapping['properties'][self.embedding_field]['type']}'. Please update the "
                        f"document_store to use a different name for the embedding_field parameter."
                    )
                mapping["properties"][self.embedding_field] = {
                    "type": "dense_vector",
                    "dims": self.embedding_dim,
                }
                response = self.client.indices.put_mapping(index=index_name, body=mapping)
                return response

        if self.custom_mapping:
            mapping = self.custom_mapping
        else:
            mapping = {
                "mappings": {
                    "properties": {
                        self.name_field: {"type": "keyword"},
                        self.content_field: {"type": "text"},
                    },
                    "dynamic_templates": [
                        {
                            "strings": {
                                "path_match": "*",
                                "match_mapping_type": "string",
                                "mapping": {"type": "keyword"},
                            }
                        }
                    ],
                },
                "settings": {
                    "analysis": {
                        "analyzer": {
                            "default": {
                                "type": self.analyzer,
                            }
                        }
                    }
                },
            }
            if self.embedding_field:
                mapping["mappings"]["properties"][self.embedding_field] = {
                    "type": "dense_vector",
                    "dims": self.embedding_dim,
                }

        try:
            response = self.client.indices.create(index=index_name, body=mapping)
        except RequestError as e:
            if not self.client.indices.exists(index=index_name):
                raise e
        return response

    def _convert_es_hit_to_document(
        self,
        hit: dict,
        return_embedding: bool,
        adapt_score_for_embedding: bool = False,
    ) -> Document:
        # We put all additional data of the doc into meta_data and return it in the API
        meta_data = {
            k: v for k, v in hit["_source"].items() if k not in (self.content_field, "content_type", self.embedding_field)
        }
        name = meta_data.pop(self.name_field, None)
        if name:
            meta_data["name"] = name

        score = hit["_score"] if hit["_score"] else None
        if score:
            if adapt_score_for_embedding:
                score = self._scale_embedding_score(score)
                if self.similarity == "cosine":
                    probability = (score + 1) / 2  # scaling probability from cosine similarity
                elif self.similarity == "dot_product":
                    probability = float(expit(np.asarray(score / 100)))  # scaling probability from dot product
            else:
                probability = float(expit(np.asarray(score / 8)))  # scaling probability from TFIDF/BM25
        else:
            probability = None

        embedding = None
        if return_embedding:
            embedding_list = hit["_source"].get(self.embedding_field)
            if embedding_list:
                embedding = np.asarray(embedding_list, dtype=np.float32)

        document = Document(
            id=hit["_id"],
            text=hit["_source"].get(self.content_field),
            meta=meta_data,
            score=score,
            probability=probability,
            embedding=embedding,
        )

        return document

    def _get_all_documents_in_index(
        self,
        index: str,
        filters: Optional[Dict[str, List[str]]] = None,
        batch_size: int = 10_000,
        only_documents_without_embedding: bool = False,
    ) -> Generator[dict, None, None]:
        """
        Return all documents in a specific index in the document store
        """
        body: dict = {"query": {"bool": {}}}

        if filters:
            filter_clause = []
            for k, vs in filters.items():
                filter_clause.append({"terms": {k: vs}})
            body["query"]["bool"]["filter"] = filter_clause

        if only_documents_without_embedding:
            body['query']['bool']['must_not'] = [{"exists": {"field": self.embedding_field}}]

        result = scan(self.client, query=body, index=index, size=batch_size, scroll=self.scroll)
        yield from result

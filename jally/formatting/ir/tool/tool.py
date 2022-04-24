import copy
import itertools
import logging
import re
import string
from typing import Callable, Dict, List, Union

import numpy as np
from jally.ir.document_store import base
from more_itertools import windowed

logger = logging.getLogger(__name__)


def get_unique_docs(data: List[Union[dict, base.Document]], field_map: dict) -> List[base.Document]:
    docs = []
    buffer = set()
    for doc in data:
        doc = base.Document.from_dict(doc, field_map=field_map) if isinstance(doc, dict) else doc
        if doc.id in buffer:
            continue
        buffer.add(doc.id)
        docs.append(doc)
    return docs


def flatten_list(nested_list):
    """Flatten an arbitrarily nested list, without recursion (to avoid
    stack overflows). Returns a new list, the original list is unchanged.
    >> list(flatten_list([1, 2, 3, [4], [], [[[[[[[[[5]]]]]]]]]]))
    [1, 2, 3, 4, 5]
    >> list(flatten_list([[1, 2], 3]))
    [1, 2, 3]
    """
    nested_list = copy.deepcopy(nested_list)

    while nested_list:
        sublist = nested_list.pop(0)

        if isinstance(sublist, list):
            nested_list = sublist + nested_list
        else:
            yield sublist


def get_batches_from_generator(iterable, n):
    """
    Batch elements of an iterable into fixed-length chunks or blocks.
    """
    it = iter(iterable)
    x = tuple(itertools.islice(it, n))
    while x:
        yield x
        x = tuple(itertools.islice(it, n))


def chunked_dict(dictionary, size):
    it = iter(dictionary)
    for i in range(0, len(dictionary), size):
        yield {k: dictionary[k] for k in itertools.islice(it, size)}


def chunk(
    document: Union[dict, base.Document],
    chunk_length: int = 184,
    chunk_overlap: int = 64,
    on_dot: bool = True,
    _nlp: Callable = None,
) -> List[dict]:
    """
    :param document:
    :return: List[Document]
    """

    def wrap_return(txt: List[str]) -> List[dict]:
        documents = []
        for i, txt in enumerate(txt_chunks):
            doc = copy.deepcopy(document)
            doc["text"] = txt
            if "meta" not in doc.keys() or doc["meta"] is None:
                doc["meta"] = {}
            doc["meta"]["chunk_id"] = i
            documents.append(doc)
        return documents

    if isinstance(document, base.Document):
        document = document.to_dict()
    text = document['text']
    sents = _nlp(text).sents
    if not on_dot:
        result = []
        segments = list([w for s in sents for w in s.text.split()])
        for seg in windowed(segments, n=chunk_length, step=chunk_length - chunk_overlap):
            result.append(' '.join(list(seg)))
        return wrap_return(result)
    word_cnt = 0
    chunks = []
    cur_chunk = []
    for sen in sents:
        cur_word_cnt = len(sen.text.split())
        if cur_word_cnt > chunk_length:
            logger.warning(f'Sentence \"{sen}\" contains {str(cur_word_cnt)} words. which is more than {str(chunk_length)}.')
        if word_cnt + cur_word_cnt > chunk_length:
            if len(cur_chunk) > 0:
                chunks.append(cur_chunk)
            overlap = []
            cnt = 0
            for candidate in reversed(cur_chunk):
                seq_len = len(candidate.split())
                if cnt + seq_len < chunk_overlap:
                    overlap.append(candidate)
                    cnt += seq_len
                else:
                    break
            cur_chunk = list(reversed(overlap))
            word_cnt = cnt
        cur_chunk.append(str(sen))
        word_cnt += cur_word_cnt
    if cur_chunk:
        chunks.append(cur_chunk)
    txt_chunks = [' '.join(_chunk) for _chunk in chunks]

    return wrap_return(txt_chunks)


def format_to_str(arg: Union[Union[Union[str, Dict], base.Document], List[str]]) -> str:
    if isinstance(arg, str):
        return arg
    arg = arg.to_dict() if isinstance(arg, base.Document) else arg
    return arg["text"]


def format_document(s: str) -> List[str]:
    """
    Lower text and remove punctuation, articles and extra whitespace.
    """

    def remove_articles(text):
        regex = re.compile(r'\b(a|an|the)\b', re.UNICODE)
        return re.sub(regex, ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def get_tokens(s: str) -> List[str]:
    if not s:
        return []
    return format_document(s).split()


def elastic_query_api(
    query_emb: np.ndarray, top_k: int = 10, embedding_field="embedding", similarity="dot_product", mode: str = "strict"
):
    """
    Generate Elasticsearch query for vector similarity.
    """
    if similarity == "cosine":
        similarity_fn_name = "cosineSimilarity"
    elif similarity == "dot_product":
        similarity_fn_name = "dotProduct"
    else:
        raise Exception("Invalid value for similarity in ElasticDocStore. Either \'cosine\' or \'dot_product\'")

    # To handle scenarios where embeddings may be missing
    script_score_query: dict = {"match_all": {}}
    if mode == "strict":
        script_score_query = {"bool": {"filter": {"bool": {"must": [{"exists": {"field": embedding_field}}]}}}}

    query = {
        "script_score": {
            "query": script_score_query,
            "script": {
                # offset score to ensure a positive range as required by Elasticsearch
                "source": f"{similarity_fn_name}(params.query_vector,'{embedding_field}') + 1000",
                "params": {"query_vector": query_emb.tolist()},
            },
        }
    }
    return query


def sql_query_api():
    raise NotImplementedError()

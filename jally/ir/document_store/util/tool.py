import ast
import copy
import itertools
import json
import pathlib
from typing import Union

import numpy as np
import random_name
import simplejson
from jally.ir.document_store import base


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


def load(data_dir: Union[pathlib.Path, str], filename: str, embedding_field="embedding", load_embedding=True, ext=".json"):
    data_dir = pathlib.Path(data_dir)
    db_filename = filename
    db_filepath = data_dir / (db_filename + ext)

    with open(str(db_filepath), "r", encoding="utf-8") as j_ptr:
        docs = json.load(j_ptr)

    for d in docs:
        if "meta" in d.keys():
            try:
                d["meta"] = ast.literal_eval(d["meta"])
            except ValueError as e:
                continue

    if embedding_field is not None:
        if load_embedding:
            index_filename = filename + "_index" + ".npy"
            index_filepath = data_dir / index_filename
            embeddings = np.load(str(index_filepath))
            for iDoc, iEmb in zip(docs, embeddings):
                iDoc[embedding_field] = iEmb
        else:
            for iDoc in docs:
                iDoc[embedding_field] = np.nan

    return docs


def save(data, data_dir: Union[str, pathlib.Path], embedding_field="embedding", save_embedding=True, ext=".json"):
    data_dir = pathlib.Path(data_dir)
    data_dir.parent.mkdir(parents=True, exist_ok=True)
    db_filename = random_name.generate_name()
    index_filename = db_filename + "_index" + ".npy"

    db_filepath = data_dir / (db_filename + ext)
    index_filepath = data_dir / index_filename

    if embedding_field is not None:
        if save_embedding:
            index_data = []
            for dic in data:
                index_data.append(copy.deepcopy(dic[embedding_field]))
                dic[embedding_field] = np.nan
            np.save(index_filepath, np.array(index_data))
        else:
            for dic in data:
                dic[embedding_field] = np.nan

    with open(str(db_filepath), 'w', encoding='utf-8-sig') as j_ptr:
        simplejson.dump(data, j_ptr, indent=4, ensure_ascii=False, ignore_nan=True)

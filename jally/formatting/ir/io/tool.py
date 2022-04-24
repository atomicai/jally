import ast
import copy
import json
import pathlib
from typing import Union

import numpy as np
import random_name
import simplejson


def load(
    data_dir: Union[pathlib.Path, str],
    filename: str,
    embedding_field="embedding",
    load_embedding=True,
    ext=".json",
    parse_meta: bool = False,
    lazy: bool = False,
):
    data_dir = pathlib.Path(data_dir)
    db_filename = filename
    db_filepath = data_dir / (db_filename + ext)

    with open(str(db_filepath), "r", encoding="utf-8-sig") as j_ptr:
        if lazy:
            for jline in j_ptr:
                yield json.loads(jline)
        else:
            docs = json.load(j_ptr)

    if lazy:
        raise StopIteration

    if parse_meta:
        for d in docs:
            d["meta"] = ast.literal_eval(d["meta"])

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

    yield docs


def save(data, data_dir: Union[str, pathlib.Path], embedding_field="embedding", save_embedding=True, ext=".json"):
    data_dir = pathlib.Path(data_dir)
    data_dir.parent.mkdir(parents=True, exist_ok=True)
    db_filename = random_name.generate_name()

    db_filepath = data_dir / (db_filename + ext)

    if embedding_field is not None:
        if save_embedding:
            index_filename = db_filename + "_index" + ".npy"
            index_filepath = data_dir / index_filename
            index_data = []
            for dic in data:
                index_data.append(copy.deepcopy(dic[embedding_field]))
                dic[embedding_field] = np.nan
            np.save(index_filepath, np.array(index_data))
        else:
            for dic in data:
                dic[embedding_field] = np.nan
    else:
        pass

    with open(str(db_filepath), 'w', encoding='utf-8-sig') as j_ptr:
        simplejson.dump(data, j_ptr, indent=4, ensure_ascii=False, ignore_nan=True)

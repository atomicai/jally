import json
import logging
import pathlib
import random
import uuid
from typing import Dict, List, Union

from nlp.formatting.ir import io as io_tool
from nlp.processing.ir.base import Processor as BaseProcessor
from nlp.processing.ir.tunnel import base

logger = logging.getLogger(__name__)


class BiAdaptiveProcessor(base.BaseAdaptiveProcessor):
    def __init__(
        self,
        query_processor: BaseProcessor,
        passage_processor: BaseProcessor,
        max_seq_len_query: int = 128,
        max_seq_len_passage: int = 384,
        max_samples: int = 8,
        num_hard_neg: int = 1,
        num_hard_pos: int = 1,
        **kwargs,
    ):
        self.qp = query_processor
        self.pp = passage_processor
        self.qn = max_seq_len_query
        self.pn = max_seq_len_passage
        self.max_samples = max_samples
        self.num_hard_neg = num_hard_neg
        self.num_hard_pos = num_hard_pos

    def dataset_from_dicts(self, dicts):
        pass

    def file_to_dicts(self, filepath: Union[str, pathlib.Path]) -> List[Dict]:
        """
        Converts a Dense Passage Retrieval (DPR) data file in json format to a list of dictionaries.

        :param file: filename of DPR data in json format
                Each sample is a dictionary of format:
                {"title": str,
                "query": str,
                "answers": list of str
                "positive_ctxs": list of dictionaries of format {'title': str, 'text': str, 'score': int, 'title_score': int, 'passage_id': str}
                "negative_ctxs": list of dictionaries of format {'title': str, 'text': str, 'score': int, 'title_score': int, 'passage_id': str}
                "hard_negative_ctxs": list of dictionaries of format {'title': str, 'text': str, 'score': int, 'title_score': int, 'passage_id': str}
                }


        Returns:
        list of dictionaries: List[dict]
            each dictionary:
            {"query": str,
            "passages": [{"text": document_text, "title": xxx, "label": "hard_positive", "external_id": abb123},
            {"text": document_text, "title": xxx, "label": "hard_negative", "external_id": abb134},
            ...]}
        """
        path = pathlib.Path(filepath)
        docs = io_tool.load(path.parent, filename=path.name, embedding_field=None, load_embedding=False)
        docs = random.sample(docs, min(self.max_samples, len(docs)))

        # convert DPR dictionary to standard dictionary
        query_key = ["query"]
        hard_pos_key = ["hard_pos_ctx"]
        hard_neg_key = ["hard_neg_ctx"]
        ans = []
        for i, i_doc in enumerate(docs):
            sample = {}
            passages = []
            for key, val in i_doc.items():
                if key in query_key:
                    sample["query"] = val
                elif key in hard_pos_key:
                    random.shuffle(val)
                    for pos_doc in val[: self.num_hard_pos]:
                        passages.append(
                            {
                                "title": pos_doc.get("title", ""),
                                "text": pos_doc["text"],
                                "label": "hard_positive",
                                "external_id": pos_doc.get("passage_id", uuid.uuid4().hex.upper()[0:8]),
                            }
                        )
                elif key in hard_neg_key:
                    random.shuffle(val)
                    for neg_doc in val[: self.num_hard_neg]:
                        passages.append(
                            {
                                "title": neg_doc.get("title", ""),
                                "text": neg_doc["text"],
                                "label": "hard_negative",
                                "external_id": neg_doc.get("passage_id", uuid.uuid4().hex.upper()[0:8]),
                            }
                        )
                else:
                    raise ValueError(f"WTF the key \"{key}\" is in the training example {str(i)}")
            sample["passages"] = passages
            ans.append(sample)
        return ans

import pathlib
from typing import Dict, List, Optional

from jally.processing.ir import base
from jally.processing.ir.tool import Sample, SampleBasket, create_dataset
from transformers import AutoTokenizer


class IProcessor(base.Processor, calling_name="dpr_wiki_768"):
    def __init__(self, max_seq_len_query: int = 128):
        self.query_tokenizer = None
        self.max_seq_len_query = max_seq_len_query

    @classmethod
    def load(cls, query_tokenizer_name: str = "facebook/dpr-question_encoder-single-nq-base", use_fast: bool = True, **kwargs):

        processor = cls(**kwargs)

        if query_tokenizer_name is None:
            query_tokenizer_name = cls.model_names[0]
        processor.query_tokenizer = AutoTokenizer.from_pretrained(query_tokenizer_name, use_fast=use_fast)

        return processor

    def save(self, save_dir: pathlib.Path, **kwargs):
        self.query_tokenizer.save_pretrained(save_dir)

    def preprocess(self, txt: str) -> str:
        return txt.lower()

    def _tokenize(self, baskets):

        for i, basket in enumerate(baskets):

            clear_text = {}
            tokenized = {}
            features = {}

            try:
                q_text = self.preprocess(basket.raw["query"])

                query_inputs = self.query_tokenizer.encode_plus(
                    text=q_text,
                    max_length=self.max_seq_len_query,
                    add_special_tokens=True,
                    truncation=True,
                    truncation_strategy="longest_first",
                    padding="max_length",
                    return_token_type_ids=True,
                )

                tokenized_query = self.query_tokenizer.convert_ids_to_tokens(query_inputs["input_ids"])

                clear_text["query_text"] = q_text
                tokenized["query_tokens"] = tokenized_query

                features["query_input_ids"] = query_inputs["input_ids"]
                features["query_segment_ids"] = query_inputs["token_type_ids"]
                features["query_attention_mask"] = query_inputs["attention_mask"]

                sample = Sample(
                    _id=None,
                    clear_text=clear_text,
                    tokenized=tokenized,
                    features=features,
                )

                basket.samples = [sample]

            except Exception as e:
                # TODO: Добавить логгинги и проч...
                pass

        return baskets

    def dataset_from_dicts(self, dicts: List[Dict], return_baskets: bool = True):
        baskets = []
        for d, in_batch_id in zip(dicts, range(len(dicts))):
            basket = SampleBasket(id_external=None, id_internal=in_batch_id, raw=d)
            baskets.append(basket)

        baskets = self._tokenize(baskets)

        # Convert features into pytorch dataset, this step also removes and logs potential errors during preprocessing
        dataset, tensor_names, problematic_ids, baskets = create_dataset(baskets)
        if return_baskets:
            return dataset, tensor_names, problematic_ids, baskets
        else:
            return dataset, tensor_names, problematic_ids


class TProcessor(IProcessor, calling_name="twitter"):
    def __init__(self, max_seq_len_query: int = 128):
        super(TProcessor, self).__init__(max_seq_len_query=max_seq_len_query)

    @classmethod
    def load(cls, query_tokenizer_name: str = "distilbert-base-multilingual-cased", use_fast: bool = True, **kwargs):

        processor = cls(**kwargs)

        processor.query_tokenizer = AutoTokenizer.from_pretrained(query_tokenizer_name, use_fast=use_fast)

        return processor

    def preprocess(self, txt: str) -> str:
        return txt

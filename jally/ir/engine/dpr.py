import os
import pathlib
from typing import Dict, List, Optional, Type, Union

import numpy as np
import torch
from jally.modeling.ir.module import dpr
from jally.processing.ir import dpr as proc_dpr
from jally.processing.ir import tool
from more_itertools import chunked
from nlp.ir.document_store import base as base_doc
from nlp.ir.engine import base as base_engine
from torch.utils import data


class DenseRetriever(base_engine.IR):
    def __init__(
        self,
        store_or_store_name: Union[str, Type[base_doc.BaseDocStore]] = None,
        query_processor_name_or_path: Optional[Union[str, pathlib.Path]] = None,
        query_model_name_or_path: Optional[Union[str, pathlib.Path]] = None,
        config: Dict = None,
    ) -> None:
        config = dict() if config is None else config
        if query_processor_name_or_path is None:
            query_processor_name_or_path = os.environ.get('RETRIEVER_QUERY_WEIGHTS', None)
        query_processor = proc_dpr.IProcessor.load(
            query_tokenizer_name=query_processor_name_or_path, max_seq_len_query=config.get("max_seq_len_query", 128)
        )

        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        if query_model_name_or_path is None:
            query_model_name_or_path = os.environ.get('RETRIEVER_QUERY_WEIGHTS', None)
        query_model = dpr.DEncoder.load(query_model_name_or_path)
        query_model = query_model.to(device)
        query_model.eval()

        store = store_or_store_name

        super(DenseRetriever, self).__init__(store, query_processor, query_model)
        self.top_k = config.get("top_k", 10)
        self.batch_size = config.get("batch_size", 1)
        self.return_embedding = config.get("return_embedding", False)

    def _search_store(self, query_embedding: np.array, index: str):
        return self.store.query_by_embedding(
            query_embedding,
            top_k=self.top_k,
            index=index,
            return_embedding=self.return_embedding,
        )

    def retrieve_top_k(
        self, query: Union[str, List[Dict]], index: Optional[str] = "document", **kwargs
    ) -> List[base_doc.Document]:
        """Returns top k relevant documents ranked by relevance(likely <query, document> dot product)

        Parameters:
        query (Union[str, List[Dict]]): either a single query or batch of {"query": query} dicts
        index (str, optional): store parametr representing domain.
        Default value for milvus storage is "document"


        Returns:
        List[base.Document]:List of documents sorted by relevance decreasing

        """
        # TODO: How big should batch be to spawn separate processes ?
        # Would there be any conflict(s) with Fast tokenizers back by huggingface.
        # P.S There are warning thrown by transformers
        # indicating Python multiprocessing may result in deadlock with rust tokenizers.
        # Our InferenceDPRProcessor is backed by `transformers` fast tokenizer.
        if not self.use_st:
            query = [{"query": query}]
            dataset, tensor_names, _, baskets = self.query_processor.dataset_from_dicts(query)
            data_loader = tool.NamedDataLoader(
                dataset=dataset,
                sampler=data.SequentialSampler(dataset),
                batch_size=self.batch_size,
                tensor_names=tensor_names,
            )
        else:
            data_loader = chunked(query, n=self.batch_size)

        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        for batch in data_loader:
            batch = {key: batch[key].to(device) for key in batch} if not self.use_st else batch

            with torch.no_grad():
                model_output = self.query_model(**batch) if not self.use_st else self.query_model.encode(batch)
                # model_output = self.query_model(
                #     input_ids=batch["query_input_ids"],
                #     segment_ids=batch["query_segment_ids"],
                #     padding_mask=batch["query_attention_mask"],
                # )

            query_embeds = model_output.cpu().numpy() if not self.use_st else model_output
            # TODO: do it parallel?
            response = []

            for query_embed in query_embeds:
                response.append(self._search_store(query_embed, index))

            yield response

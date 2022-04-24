import abc
from typing import Dict, List, Optional, Union

from jally.ir.document_store import base
from jally.modeling.ir.module.base import LanguageModel
from jally.processing.ir.base import processor


class IR(abc.ABC):
    def __init__(
        self,
        store: base.BaseDocStore,
        query_processor: processor.Processor,
        query_model: LanguageModel,
    ) -> None:
        self.store = store
        self.query_processor = query_processor
        self.query_model = query_model

    @abc.abstractmethod
    def retrieve_top_k(
        self, query_batch: List[Dict], index: Optional[str] = "document", top_k: Optional[int] = 5, **kwargs
    ) -> List[Union[Dict, base.Document]]:
        pass


class IRGenerator(abc.ABC):
    def __init__(self, retriever: IR) -> None:
        self.retriever = retriever

    @abc.abstractmethod
    def generate(self, query: str, index: Optional[str] = "document", **kwargs) -> List[Union[Dict, base.Document]]:
        pass

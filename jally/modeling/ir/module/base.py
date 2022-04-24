import abc
import pathlib
from typing import Any, Dict, List, Optional, Union

import torch
import transformers
from jally.ir.document_store import base


class ProjectionHead(torch.nn.Module, abc.ABC):
    @abc.abstractmethod
    def forward(
        self, input: transformers.modeling_outputs.BaseModelOutput, *args, **kwargs
    ) -> transformers.modeling_outputs.BaseModelOutput:
        pass

    def __init__(self):
        super(ProjectionHead, self).__init__()


class FeedForwardModule(torch.nn.Module):
    """A feed forward neural network of variable depth and width."""

    def __init__(self, layer_dims: List[int]) -> None:
        super(FeedForwardModule, self).__init__()
        self.layer_dims = layer_dims
        layers = []

        for size_in, size_out in zip(layer_dims[:-1], layer_dims[1:]):
            layer = torch.nn.Linear(size_in, size_out)
            layers.append(layer)
        self.feed_forward = torch.nn.Sequential(*layers)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        logits = self.feed_forward(input)
        return logits


class LanguageModel(torch.nn.Module):
    """
    The main class wrapping different huggingface model(s). The main reason is "HF" forward pass require different params for various LM.
    E.g. Distilled BERT doesn't have segment_ids
    """

    subclasses = {}

    def __init_subclass__(cls, calling_name: str = None, **kwargs):
        """This automatically keeps track of all available subclasses.
        Enables generic load() or all specific Formatter implementation.
        """
        super().__init_subclass__(**kwargs)
        calling_name = cls.__name__ if calling_name is None else calling_name
        cls.subclasses[calling_name] = cls

    @classmethod
    def load(cls, name: str = None, **kwargs):
        klass = cls.subclasses[name] if name is not None else cls.subclasses[cls.__name__]
        return klass.load(**kwargs)

    @abc.abstractmethod
    def save(self, save_dir: Union[str, pathlib.Path], **kwargs):
        pass


class IRGenerator(abc.ABC):
    @abc.abstractmethod
    def predict(self, query: str, documents: List[base.Document], top_k: Optional[int]) -> Dict:
        pass

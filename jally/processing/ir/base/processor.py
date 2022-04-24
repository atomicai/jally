import abc
import pathlib
from typing import Dict, List, Optional, Union


class Processor(abc.ABC):

    subclasses = {}

    def __init_subclass__(cls, calling_name: str = None, **kwargs):
        """This automatically keeps track of all available subclasses.
        Enables generic load() or all specific `Processor` implementation.
        """
        super().__init_subclass__(**kwargs)
        calling_name = cls.__name__ if calling_name is None else calling_name
        cls.subclasses[calling_name] = cls

    @classmethod
    def load(cls, name: str = None, **kwargs):
        klass = cls.subclasses[name] if name is not None else cls.subclasses[cls.__name__]
        return klass.load(**kwargs)

    @abc.abstractmethod
    def dataset_from_dicts(self, dicts: List[Dict]):
        pass

    @abc.abstractmethod
    def preprocess(self, txt: str, **kwargs) -> str:
        pass

    @classmethod
    @abc.abstractmethod
    def save(cls, **kwargs):
        pass

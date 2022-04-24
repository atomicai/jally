import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset, TensorDataset


class SampleBasket:
    def __init__(self, id_internal: str, raw: dict, id_external=None, samples=None):
        """
        :param id_internal: Внутрибатчевый айдишник
        :type id_internal: str
        :param id_external: Для пробрасывания в другие модули...
        :type external_id: str
        :param raw: Contains the various data needed to form a sample. It is ideally in human readable form.
        :type raw: dict
        :param samples: An optional list of Samples used to populate the basket at initialization.
        :type samples: Sample
        """
        self.id_internal = id_internal
        self.id_external = id_external
        self.raw = raw
        self.samples = samples


class Sample(object):
    """A single training/test sample."""

    def __init__(self, _id, clear_text, tokenized=None, features=None):
        """
        :param _id: Чтобы, если упал на каком-то примере, найти этот пример
        :type _id: str
        :param clear_text:
        :type clear_text: dict
        :param tokenized:Разбитый на word-piece токены, которые в словаре есть
        :type tokenized: dict
        :param features: Это все, что надо, чтобы впихнуть аргументом в transformers.model(...)
        :type features: dict

        """
        self.id = _id
        self.clear_text = clear_text
        self.features = features
        self.tokenized = tokenized


def create_dataset(baskets):
    """
    Convert python features into pytorch dataset.
    Also removes potential errors during preprocessing.
    Flattens nested basket structure to create a flat list of features
    """
    features_flat = []
    basket_to_remove = []
    problem_ids = []  # TODO:

    for basket in baskets:
        for sample in basket.samples:
            features_flat.append(sample.features)

    tensor_names = list(features_flat[0].keys())
    all_tensors = []
    for t_name in tensor_names:
        try:
            cur_tensor = torch.tensor([sample[t_name] for sample in features_flat], dtype=torch.long)
        except Exception as e:
            # TODO:
            pass
        all_tensors.append(cur_tensor)

    dataset = TensorDataset(*all_tensors)
    return dataset, tensor_names, problem_ids, baskets


class NamedDataLoader(DataLoader):
    """
    A modified version of the PyTorch DataLoader that returns a dictionary where the key is
    the name of the tensor and the value is the tensor itself.
    """

    def __init__(
        self,
        dataset,
        batch_size,
        sampler=None,
        tensor_names=None,
        num_workers=0,
        pin_memory=False,
    ):
        """
        :param dataset: The dataset that will be wrapped by this NamedDataLoader
        :type dataset: Dataset
        :param sampler: The sampler used by the NamedDataLoader to choose which samples to include in the batch
        :type sampler: Sampler
        :param batch_size: The size of the batch to be returned by the NamedDataLoader
        :type batch_size: int
        :param tensor_names: The names of the tensor, in the order that the dataset returns them in.
        :type tensor_names: list
        :param num_workers: number of workers to use for the DataLoader
        :type num_workers: int
        :param pin_memory: argument for Data Loader to use page-locked memory for faster transfer of data to GPU
        :type pin_memory: bool
        """

        def collate_fn(batch):
            """
            A custom collate function that formats the batch as a dictionary where the key is
            the name of the tensor and the value is the tensor itself
            """

            if type(dataset).__name__ == "_StreamingDataSet":
                _tensor_names = dataset.tensor_names
            else:
                _tensor_names = tensor_names

            if type(batch[0]) == list:
                batch = batch[0]

            assert len(batch[0]) == len(
                _tensor_names
            ), "Dataset contains {} tensors while there are {} tensor names supplied: {}".format(
                len(batch[0]), len(_tensor_names), _tensor_names
            )
            lists_temp = [[] for _ in range(len(_tensor_names))]
            ret = dict(zip(_tensor_names, lists_temp))

            for example in batch:
                for name, tensor in zip(_tensor_names, example):
                    ret[name].append(tensor)

            for key in ret:
                ret[key] = torch.stack(ret[key])

            return ret

        super(NamedDataLoader, self).__init__(
            dataset=dataset,
            sampler=sampler,
            batch_size=batch_size,
            collate_fn=collate_fn,
            pin_memory=pin_memory,
            num_workers=num_workers,
        )

    def __len__(self):
        if type(self.dataset).__name__ == "_StreamingDataSet":
            num_samples = len(self.dataset)
            num_batches = np.ceil(num_samples / self.dataset.batch_size)
            return num_batches
        else:
            return super().__len__()

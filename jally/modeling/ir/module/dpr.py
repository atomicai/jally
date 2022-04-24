import logging
import os
import pathlib
from typing import Optional, Tuple, Union

import torch
import transformers
from icecream import ic
from jally.modeling.ir.module import base
from transformers import modeling_outputs
from transformers.modeling_utils import SequenceSummary

logger = logging.getLogger(__name__)


# These are the names of the attributes in various model configs which refer to the number of dimensions
# in the output vectors
OUTPUT_DIM_NAMES = ["dim", "hidden_size", "d_model"]


class DPREncoder(base.LanguageModel, calling_name="dpr_wiki_768"):
    def __init__(
        self,
        model: transformers.PreTrainedModel,
        proj_head: Optional[base.ProjectionHead] = None,
    ) -> None:
        super(DPREncoder, self).__init__()
        self.model = model
        self.proj = proj_head

    def save(self, output_dir: Union[str, pathlib.Path]):
        output_dir = pathlib.Path(output_dir)
        self.model.save_pretrained(str(output_dir))
        model_dict = self.state_dict()
        hf_weight_keys = [k for k in model_dict.keys() if k.startswith("model")]
        for k in hf_weight_keys:
            model_dict.pop(k)
        if self.proj:
            torch.save(model_dict, os.path.join(output_dir, "proj_head.pt"))

    @classmethod
    def load(cls, path: Union[pathlib.Path, str], **model_args):
        hf_model = transformers.AutoModel.from_pretrained(path)
        model = cls(hf_model, **model_args)
        proj_head_path = pathlib.Path(path) / "proj_head.pt"
        if proj_head_path.exists():
            model_dict = torch.load(proj_head_path, map_location="cpu")
            model.load_state_dict(model_dict, strict=False)
        return model

    def get_output_dims(self):
        config = self.model.config
        for odn in OUTPUT_DIM_NAMES:
            if odn in dir(config):
                return getattr(config, odn)
        else:
            raise Exception("Could not infer the output dimensions of the language model")

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        token_type_ids: Optional[torch.Tensor] = None,
        inputs_embeds: Optional[torch.Tensor] = None,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
        return_dict: bool = False,
        **kwargs
    ) -> Union[modeling_outputs.BaseModelOutputWithPooling, Tuple[torch.Tensor, ...]]:
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )
        if self.proj:
            outputs = self.proj(outputs)
        return outputs


class DEncoder(DPREncoder, calling_name="dpr_distill_768_512"):
    """`Distilled` encoder
    Wrapper for distilled version of enoder(s). Mainly for two reasons:
     - They don't have `token_type_ids`...
     - They don't provide `pooled_output` by default. So we add some to stay on par with interface.

     See https://discuss.huggingface.co/t/why-is-there-no-pooler-representation-for-xlnet-or-a-consistent-use-of-sequence-summary/2357/4

    Args:
        DEncoder (_type_): allows
    """

    def __init__(
        self, model: transformers.PreTrainedModel, proj_head: Optional[base.ProjectionHead] = None, dropout: float = 0.1
    ) -> None:
        super(DEncoder, self).__init__(model=model, proj_head=proj_head)
        config = self.model.config
        config.summary_last_dropout = 0
        config.summary_type = 'last'
        config.summary_activation = 'tanh'
        self.pooler = SequenceSummary(config)
        # DistilBERT does not provide a pooled_output by default. Therefore, we need to initialize an extra pooler.
        # The pooler takes the first hidden representation & feeds it to a dense layer of (hidden_dim x hidden_dim).
        # We don't want a dropout in the end of the pooler, since we do that already in the adaptive model before we
        # feed everything to the prediction head
        config.summary_last_dropout = 0
        config.summary_type = 'first'
        config.summary_activation = 'tanh'
        self.name = config._name_or_path
        self.dropout = torch.nn.Dropout(dropout)

    def forward(
        self,
        query_input_ids: torch.Tensor,
        query_segment_ids: torch.Tensor = None,
        query_attention_mask: torch.Tensor = None,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
        return_dict: bool = False,
        **kwargs
    ):
        output = self.model(
            input_ids=query_input_ids,
            attention_mask=query_attention_mask,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )
        # Need to call it manually!
        pooled_output = self.pooler(output[0])
        output = self.dropout(pooled_output)
        return output


class IEncoder(DPREncoder, calling_name="dpr_wiki_query_768"):
    def __init__(
        self, model: transformers.PreTrainedModel, proj_head: Optional[base.ProjectionHead] = None, dropout: float = 0.1
    ) -> None:
        super(IEncoder, self).__init__(model=model, proj_head=proj_head)
        self.dropout = torch.nn.Dropout(dropout)

    @classmethod
    def load(cls, name: Union[str, pathlib.Path] = "facebook/dpr-question_encoder-single-nq-base", **kwargs):
        return super(IEncoder, cls).load(name, **kwargs)

    def forward(
        self,
        query_input_ids: torch.Tensor,
        query_segment_ids: torch.Tensor = None,
        query_attention_mask: torch.Tensor = None,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
        return_dict: bool = False,
        **kwargs
    ):
        output = super().forward(
            input_ids=query_input_ids,
            attention_mask=query_attention_mask,
            token_type_ids=query_segment_ids,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )
        ic(output[0].shape)
        output = self.dropout(output[0])
        return output


class PEncoder(DPREncoder, calling_name="dpr_wiki_passage_768"):
    def __init__(
        self,
        model: transformers.PreTrainedModel,
        proj_head: Optional[base.ProjectionHead] = None,
    ) -> None:
        super(PEncoder, self).__init__(model=model, proj_head=proj_head)

    @classmethod
    def load(cls, name: Union[str, pathlib.Path] = "facebook/dpr-ctx_encoder-single-nq-base", **kwargs):
        return super(PEncoder, cls).load(name, **kwargs)

    def forward(
        self,
        passage_input_ids: torch.Tensor,
        passage_segment_ids: torch.Tensor = None,
        passage_attention_mask: torch.Tensor = None,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
        return_dict: bool = False,
        **kwargs
    ):
        return super().forward(
            input_ids=passage_input_ids,
            attention_mask=passage_attention_mask,
            token_type_ids=passage_segment_ids,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

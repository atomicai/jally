import logging
from typing import List

import torch
from jally.modeling.ir.module import base
from torch import nn
from transformers import modeling_outputs

logger = logging.getLogger(__name__)


class FFHead(base.ProjectionHead):
    def __init__(self, layer_dims: List[int], norm_input: bool = False, norm_output: bool = False) -> None:
        super(FFHead, self).__init__()
        self.layer_dims = layer_dims
        self.ff_module = base.FeedForwardModule(self.layer_dims)
        self.norm_in = nn.LayerNorm(layer_dims[0]) if norm_input else None
        self.norm_out = nn.LayerNorm(layer_dims[-1]) if norm_output else None

    def _output(
        self,
        input: modeling_outputs.BaseModelOutputWithPooling,
        pooler_output: torch.Tensor,
    ):
        return modeling_outputs.BaseModelOutputWithPooling(
            hidden_states=input.hidden_states,
            attentions=input.attentions,
            pooler_output=pooler_output,
        )

    def forward_norm(self, input: torch.Tensor):
        if self.norm_in:
            input = self.norm_in(input)

        logits = self.ff_module(input)

        if self.norm_out:
            logits = self.norm_out(logits)
        return logits

    def forward(self, input: modeling_outputs.BaseModelOutputWithPooling, *args, **kwargs) -> torch.Tensor:
        ff_input = input.last_hidden_state
        pooler_output = self.forward_norm(ff_input)
        return self._output(input, pooler_output)


class PoolerHead(FFHead):
    def __init__(
        self,
        input_dim: int,
        project_dim: int,
        norm_input: bool = False,
        norm_output: bool = False,
    ) -> None:
        layer_dims = [input_dim, project_dim]
        super(PoolerHead, self).__init__(layer_dims, norm_input, norm_output)

    def forward(self, input: modeling_outputs.BaseModelOutputWithPooling, *args, **kwargs) -> torch.Tensor:
        ff_input = input.last_hidden_state[:, 0]
        pooler_output = self.forward_norm(ff_input)
        return self._output(input, pooler_output)

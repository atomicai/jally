#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import TypeVar, Union, Callable, List
from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if

T = TypeVar('T')  # Any type.
ClassValueOrCallable = Union[T, Callable[['Data'], T]]
OptionalClassValueOrCallable = Union[ClassValueOrCallable[T], type(None)]
ClassValueOrCallableList = List[ClassValueOrCallable[T]]

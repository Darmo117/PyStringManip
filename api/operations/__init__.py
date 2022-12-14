import dataclasses
import inspect

import typing_inspect

from . import _docstring_parser as dsp
from ._core import *
from .data_formats import *
from .date_time import *
from .encryption import *
from .extractors import *
from .info_theory import *
from .informatics import *
from .language import *
from .math import *
from .random import *
from .strings import *


@dataclasses.dataclass(frozen=True)
class ArgMetadata:
    type: type
    default_value: typ.Any
    doc: str = None


@dataclasses.dataclass(frozen=True)
class OperationMetadata:
    name: str
    args: dict[str, ArgMetadata]
    doc: str = None
    special: bool = False


OperationsMetadada = dict[str, OperationMetadata]

_OPERATIONS = {}
_OPS_METADATA = {
    'fork': OperationMetadata(
        name='fork',
        args={'delimiter': ArgMetadata(type=str, default_value='\n', doc='The string to split on.')},
        doc='Splits the input string using the given delimiter'
            ' then treats each resulting substring in a separate thread.',
        special=True,
    ),
    'merge': OperationMetadata(
        name='merge',
        args={'joiner': ArgMetadata(type=str, default_value='\n', doc='The string to use to join each result.')},
        doc='Merges the results of all parallel pipelines that were previously forked.'
            ' Results are guaranted to be merged in the same order as the original'
            ' substrings were before they were forked.',
        special=True,
    ),
    'skip': OperationMetadata(
        name='skip',
        args={'n': ArgMetadata(type=int, default_value=1, doc='The number of operations to skip after this one.')},
        doc='Skips the next n operations. Should be reserved for debug purposes only.',
        special=True,
    ),
}


def _init():
    global _OPERATIONS, _OPS_METADATA

    for k, v in globals().items():
        if (inspect.isclass(v) and not typing_inspect.is_generic_type(v)
                and issubclass(v, Operation) and not inspect.isabstract(v)):
            # noinspection PyTypeChecker
            op_name = Operation.format_operation_name(k)
            _OPERATIONS[op_name] = v
            docstring = dsp.parse_docstring(v.__init__.__doc__)
            md_args = {
                n: ArgMetadata(type=t, default_value=v.__init__.__defaults__[i],
                               doc=s.replace('\n', ' ') if (s := docstring.params.get(n)) else '')
                for i, (n, t) in enumerate(inspect.get_annotations(v.__init__).items())
            }
            _OPS_METADATA[op_name] = OperationMetadata(
                name=op_name,
                args=md_args,
                doc=v.__doc__,
            )


_init()


def get_operations_metadata() -> OperationsMetadada:
    return _OPS_METADATA.copy()


def create_operation(name: str, **kwargs) -> Operation:
    return _OPERATIONS[name](**kwargs)

import argparse
import dataclasses
import enum
import re
import sys
import typing as typ

from api import operations as ops, pipeline as pl

OPERATION_CFG_REGEX = re.compile(r'(?P<name>\w+)(?:\[(?P<params>(?:\w+=.+?)+(?:,(?:\w+=.+?)+)*)?])?')


class SpecialCase(enum.Enum):
    FORK = 'fork'
    MERGE = 'merge'


@dataclasses.dataclass(frozen=True)
class OperationConfig:
    name: str
    args: typ.Dict[str, typ.Any] = None


@dataclasses.dataclass(frozen=True)
class Config:
    verbose: bool
    operations: typ.List[OperationConfig]


def parse_operation(raw: str, ops_metadata: ops.OperationsMetadada, index: int) -> OperationConfig:
    if match := OPERATION_CFG_REGEX.fullmatch(raw):
        op_name = match.group('name')
        if op_name not in ops_metadata:
            raise ValueError(f'undefined operation: {op_name!r} (#{index})')
        op_metadata = ops_metadata[op_name]
        raw_params = re.split(r'(?<!\\),', p) if (p := match.group('params')) else []

        def cast_value(param_name: str, param_value: str):
            try:
                return op_metadata.args[param_name].type(param_value)
            except KeyError:
                raise ValueError(f'invalid parameter {param_name!r} for operation {op_name!r} (#{index})')
            except ValueError:
                raise ValueError(
                    f'invalid value {param_value!r} for parameter {param_name!r} on operation {op_name!r} (#{index})')

        def split_param(raw_param: str) -> typ.List[str]:
            raw_param = raw_param.replace(r'\,', ',')
            if '=' not in raw_param:
                raise ValueError(f'malformed parameter {raw_param!r} for operation {op_name!r} (#{index})')
            return raw_param.split('=', 1)

        args = {
            k: cast_value(k, v)
            for k, v in map(split_param, raw_params)
        }
        return OperationConfig(name=op_name, args=args)
    raise ValueError(f'invalid operation definition: {raw!r} (#{index})')


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description='Performs a sequence of operations on a string.'
                    ' Operations are performed in the same order as specified.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    # Change the default help text for the -h action.
    # noinspection PyProtectedMember
    parser._actions[0].help = 'Show this help message and exit.'
    parser.add_argument('-v', '--verbose', action='store_true', help='Print intermediary operation results.')
    doc = ('An operation to apply to the input string.'
           ' It must be of the form `<operation>[<arg1>=<value1>,<arg2>=<value2>,…]`.\n'
           'Available operations:\n')
    ops_metadata = ops.get_operations_metadata()
    for op in ops_metadata.values():
        doc += f'  {op.name}\t{op.doc}\n'
        for arg, metadata in op.args.items():
            doc += f'    {arg}: {metadata.type.__name__} = {metadata.default_value!r}\n'
            if metadata.doc:
                doc += f'      {metadata.doc}\n'
    parser.add_argument('operations', metavar='OPERATION', nargs='*', help=doc)

    args = parser.parse_args()
    return Config(
        verbose=args.verbose,
        operations=[parse_operation(op, ops_metadata, i) for i, op in enumerate(args.operations)],
    )


def main():
    try:
        operations_config = parse_args()
    except ValueError as e:
        print('Error:', e, file=sys.stderr)
        return
    data = sys.stdin.read()

    pipeline: pl.Pipeline | pl.ParallelPipeline = pl.Pipeline(verbose=operations_config.verbose)
    for operation in operations_config.operations:
        match operation.name:
            case SpecialCase.FORK.value:
                args = {}
                if 'delimiter' in operation.args:
                    args = {'delimiter': operation.args['delimiter']}
                pipeline = pipeline.fork(**args)
            case SpecialCase.MERGE.value:
                args = {}
                if 'joiner' in operation.args:
                    args = {'joiner': operation.args['joiner']}
                pipeline = pipeline.merge(**args)
            case name:
                pipeline = pipeline.then(ops.create_operation(name, **operation.args))
    try:
        print(pipeline.execute(data))
    except Exception as e:
        print('Error:', e, file=sys.stderr)


if __name__ == '__main__':
    main()

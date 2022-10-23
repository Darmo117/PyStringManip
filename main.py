import argparse
import dataclasses
import re
import sys
import traceback
import typing as typ

from api import operations as ops, pipeline as pl

OPERATION_CFG_REGEX = re.compile(r'(?P<name>\w+)(?:\[(?P<params>(?:\w+=.*?)+(?:,(?:\w+=.*?)+)*)?])?')


@dataclasses.dataclass(frozen=True)
class OperationConfig:
    name: str
    args: typ.Dict[str, typ.Any] = None


@dataclasses.dataclass(frozen=True)
class Config:
    verbosity: int
    operations: typ.List[OperationConfig]


def parse_operation(raw: str, ops_metadata: ops.OperationsMetadada, index: int) -> OperationConfig:
    if match := OPERATION_CFG_REGEX.fullmatch(raw):
        op_name = match.group('name')
        if op_name not in ops_metadata:
            raise ValueError(f'undefined operation: {op_name!r} (#{index})')
        op_metadata = ops_metadata[op_name]
        raw_params = re.split(r'(?<!\\),', p) if (p := match.group('params')) else []

        def cast_value(param_name: str, param_value: str) -> str:
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
    else:
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
    parser.add_argument('-v', '--verbosity', action='count', default=0, help='Print intermediary operations.')
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
        verbosity=args.verbosity,
        operations=[parse_operation(op, ops_metadata, i + 1) for i, op in enumerate(args.operations)],
    )


def main():
    class SpecialOperations:
        FORK = 'fork'
        MERGE = 'merge'
        SKIP = 'skip'

    try:
        operations_config = parse_args()
    except ValueError as e:
        print('Error:', e, file=sys.stderr)
        return
    data = sys.stdin.read()

    pipeline: pl.Pipeline | pl.ParallelPipeline = pl.Pipeline(verbosity=operations_config.verbosity)
    skip = 0
    for i, operation in enumerate(operations_config.operations):
        if skip > 0:
            skip -= 1
            continue
        try:
            match operation.name:
                case SpecialOperations.FORK:
                    args = {}
                    if 'delimiter' in operation.args:
                        args = {'delimiter': operation.args['delimiter']}
                    pipeline = pipeline.fork(**args)
                case SpecialOperations.MERGE:
                    args = {}
                    if 'joiner' in operation.args:
                        args = {'joiner': operation.args['joiner']}
                    pipeline = pipeline.merge(**args)
                case SpecialOperations.SKIP:
                    skip = operation.args.get('n', 1)
                case name:
                    pipeline = pipeline.then(ops.create_operation(name, **operation.args))
        except Exception as e:
            if operations_config.verbosity >= pl.Logger.DEBUG:
                traceback.print_exc(file=sys.stderr)
            print(f'Error at operation {operation.name!r} (#{i + 1}): {e}', file=sys.stderr)
            return
    try:
        print(pipeline.execute(data))
    except Exception as e:
        if operations_config.verbosity >= pl.Logger.DEBUG:
            traceback.print_exc(file=sys.stderr)
        print('Error:', e, file=sys.stderr)


if __name__ == '__main__':
    main()

import argparse
import dataclasses
import json
import pathlib
import re
import typing as typ

from api import operations as ops

_OPERATION_CFG_REGEX = re.compile(r'(?P<name>\w+)(?:\[(?P<params>(?:\w+=.*?)+(?:,(?:\w+=.*?)+)*)?])?')


@dataclasses.dataclass(frozen=True)
class OperationConfig:
    name: str
    args: dict[str, typ.Any] = None


@dataclasses.dataclass(frozen=True)
class Config:
    verbosity: int
    fail_if_empty: bool
    operations: list[OperationConfig]


def _parse_cli_operation(raw: str, ops_metadata: ops.OperationsMetadada, index: int) -> OperationConfig:
    if match := _OPERATION_CFG_REGEX.fullmatch(raw):
        op_name = match.group('name')
        if op_name not in ops_metadata:
            raise ValueError(f'undefined operation: {op_name!r} (#{index})')
        op_metadata = ops_metadata[op_name]
        raw_params = re.split(r'(?<!\\),', p) if (p := match.group('params')) else []

        def cast_value(param_name: str, param_value: str) -> typ.Any:
            try:
                return op_metadata.args[param_name].type(param_value)
            except KeyError:
                raise ValueError(f'invalid parameter {param_name!r} for operation {op_name!r} (#{index})')
            except ValueError:
                raise ValueError(
                    f'invalid value {param_value!r} for parameter {param_name!r} on operation {op_name!r} (#{index})')

        def split_param(raw_param: str) -> list[str]:
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


def _load_config(config_path: pathlib.Path, ops_metadata: ops.OperationsMetadada) -> list[OperationConfig]:
    operations = []

    def cast_value(op_name: str, op_index: int, param_name: str, param_value: str) -> typ.Any:
        try:
            return ops_metadata[op_name].args[param_name].type(param_value)
        except KeyError:
            raise ValueError(f'invalid parameter {param_name!r} for operation {op_name!r} (#{op_index})')
        except ValueError:
            raise ValueError(
                f'invalid value {param_value!r} for parameter {param_name!r} on operation {op_name!r} (#{op_index})')

    try:
        with config_path.open(mode='r', encoding='utf8') as f:
            for i, operation in enumerate(json.load(f)['operations']):
                name = operation['name']
                if name not in ops_metadata:
                    raise ValueError(f'undefined operation: {name!r} (#{i + 1})')
                args = {
                    k: cast_value(name, i + 1, k, v)
                    for k, v in operation['params'].items()
                }
                operations.append(OperationConfig(name=name, args=args))
    except KeyError as e:
        raise ValueError(f'malformed configuration file: {e}')
    except IOError as e:
        raise ValueError(f'could not open file: {e}')
    else:
        return operations


def parse_args(args: list[str]) -> Config:
    """Parses the given CLI arguments.

    :param args: The CLI arguments.
    :return: A Config object for the arguments.
    :raises ValueError: If arguments are invalid.
    """
    parser = argparse.ArgumentParser(
        description='Performs a sequence of operations on a string.'
                    ' Operations are performed in the same order as specified.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    # Change the default help text for the -h action.
    # noinspection PyProtectedMember
    parser._actions[0].help = 'Show this help message and exit.'
    # TODO add option to display help for specific operation
    parser.add_argument('-v', '--verbosity', action='count', default=0, help='Print intermediary operations.')
    parser.add_argument('-c', '--config', metavar='FILE', type=pathlib.Path,
                        help='Path to a JSON operations configuration file.')
    parser.add_argument('-e', '--error-if-empty', action='store_true', help='Raise an error if the pipeline is empty.')
    doc = ('An operation to apply to the input string.'
           ' It must be of the form `<operation>[<arg1>=<value1>,<arg2>=<value2>,???]`.\n'
           'Available operations:\n')
    ops_metadata = ops.get_operations_metadata()
    for op in ops_metadata.values():
        doc += f'  {op.name}\t{op.doc}\n'
        for arg, metadata in op.args.items():
            doc += f'    {arg}: {metadata.type.__name__} = {metadata.default_value!r}\n'
            if metadata.doc:
                doc += f'      {metadata.doc}\n'
    doc = doc.replace('%', '%%')  # Escape '%' as parser.parse_args(...) uses %-formatting on doc string
    parser.add_argument('operations', metavar='OPERATION', nargs='*', help=doc)

    parsed_args = parser.parse_args(args)
    if parsed_args.operations and parsed_args.config:
        raise ValueError('operations cannot be specified through CLI when using -c option')
    if parsed_args.operations:
        operations = [_parse_cli_operation(op, ops_metadata, i + 1) for i, op in enumerate(parsed_args.operations)]
    else:
        operations = _load_config(parsed_args.config, ops_metadata)
    return Config(
        verbosity=parsed_args.verbosity,
        fail_if_empty=parsed_args.error_if_empty,
        operations=operations,
    )

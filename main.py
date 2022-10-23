import sys
import traceback

import config
from api import operations as ops, pipeline as pl


def main():
    class SpecialOperations:
        FORK = 'fork'
        MERGE = 'merge'
        SKIP = 'skip'

    try:
        operations_config = config.parse_args(sys.argv[1:])
    except ValueError as e:
        print('Error:', e, file=sys.stderr)
        return
    if not operations_config.operations:
        prefix = 'Error' if operations_config.fail_if_empty else 'Warning'
        print(f'{prefix}: pipeline is empty', file=sys.stderr)
        if operations_config.fail_if_empty:
            return

    if sys.stdin.isatty():
        # Print to stderr to prevent prompt from mixing with command’s actual output
        print('?>', end=' ', file=sys.stderr)
        data = input()
    else:
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
                    if skip < 0:
                        raise ValueError(f'expected positive integer, got {skip}')
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

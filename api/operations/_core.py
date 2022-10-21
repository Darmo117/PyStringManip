import abc
import re
import typing as typ


class Operation(abc.ABC):
    """An operation is a function that applies a transformation to a string."""

    @abc.abstractmethod
    def apply(self, s: str) -> str:
        """Applies this operation on the given string.

        :param s: The string to transform.
        :return: The transformed string.
        """
        pass

    def get_params(self) -> typ.Dict[str, typ.Any]:
        """Returns the configuration of this operation as a dict object.

        :return: The configuration dict.
        """
        return {}

    def __str__(self):
        op_name = self.format_operation_name(self.__class__.__name__)
        args = ",".join(f'{k}={v!r}' for k, v in sorted(self.get_params().items(), key=lambda e: e[0]))
        return f'{op_name}[{args}]'

    @staticmethod
    def format_operation_name(s: str) -> str:
        """Formats the name of an operation from CamelCase to snake_case.

        :param s: The name to format.
        :return: The formatted string.
        """
        return re.sub(r'([A-Z])', r'_\1', s)[1:].lower()

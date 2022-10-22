"""This module defines various utility functions."""


def flip_dict(d: dict) -> dict:
    """Flips all entries of the given dict object.
    If multiple entries in the input dict have the same value, only the last one will be kept.

    :param d: The dict whose entries have to be flipped.
    :return: A new dict object.
    """
    return {v: k for k, v in d.items()}


def unescape_whitespace(s: str) -> str:
    return (s.replace(r'\n', '\n')
            .replace(r'\r', '\r')
            .replace(r'\t', '\t')
            .replace(r'\f', '\f')
            .replace(r'\v', '\v'))

from __future__ import annotations

import argparse
import codecs
import io
import sys
from encodings import utf_8
from typing import Sequence
from typing import TYPE_CHECKING

from tokenize_rt import NON_CODING_TOKENS
from tokenize_rt import src_to_tokens
from tokenize_rt import Token
from tokenize_rt import tokens_to_src
from tokenize_rt import UNIMPORTANT_WS

if TYPE_CHECKING:
    from codecs import _ReadableStream
    from typing_extensions import Buffer


def _shorthand(tokens: list[Token]) -> list[Token]:
    ret: list[Token] = []
    brace_stack = []
    last_token = Token(name='OP', src='')
    for token in tokens:
        if token.name == 'OP' and token.src in '([{':
            brace_stack.append(token.src)
        elif token.name == 'OP' and token.src in ')]}':
            brace_stack.pop()

        if (
                token.name == 'NAME' and
                brace_stack and
                brace_stack[-1] == '{' and (
                    last_token.matches(name='OP', src='{') or
                    last_token.matches(name='OP', src=',')
                )
        ):
            ret.extend((
                Token(name='STRING', src=repr(token.src)),
                Token(name='OP', src=':'),
                Token(name=UNIMPORTANT_WS, src=' '),
                token,
            ))
        else:
            ret.append(token)

        if token.name != UNIMPORTANT_WS:
            last_token = token

    while ret and ret[-1].name == UNIMPORTANT_WS:
        ret.pop()

    return ret


def _make_match(
        tokens: list[Token],
        start: int,
        equals: int,
        end: int,
) -> list[Token]:
    if start > 0 and tokens[start - 1].name in {'INDENT', UNIMPORTANT_WS}:
        indent = f'{tokens[start - 1].src}{" " * 4}'
    else:
        indent = ' ' * 4

    target = tokens[start:equals]

    for expr_start in range(equals + 1, len(tokens)):
        if tokens[expr_start].name != UNIMPORTANT_WS:
            break
    expr = tokens[expr_start:end]

    error_msg = (
        f'failed to unpack!\n\n'
        f'line {tokens[start].line} | {tokens_to_src(tokens[start:end])}'
    )

    return [
        Token(name='NAME', src='match'),
        Token(name=UNIMPORTANT_WS, src=' '),
        *expr,
        Token(name='OP', src=':'),
        Token(name='NEWLINE', src='\n'),
        Token(name='INDENT', src=indent),
        Token(name='NAME', src='case'),
        Token(name=UNIMPORTANT_WS, src=' '),
        *_shorthand(target),
        Token(name='OP', src=':'),
        Token(name=UNIMPORTANT_WS, src=' '),
        Token(name='NAME', src='pass'),
        Token(name='NEWLINE', src='\n'),
        Token(name='INDENT', src=indent),
        Token(name='NAME', src='case'),
        Token(name=UNIMPORTANT_WS, src=' '),
        Token(name='NAME', src='_'),
        Token(name='OP', src=':'),
        Token(name=UNIMPORTANT_WS, src=' '),
        Token(name='CODE', src=f'raise TypeError({error_msg!r})'),
        Token(name='NEWLINE', src='\n'),
    ]


def decode(b: Buffer, errors: str = 'strict') -> tuple[str, int]:
    u, length = utf_8.decode(b, errors)
    tokens = src_to_tokens(u)

    to_replace = []
    seen_newline = True

    def _maybe_unpacking(start: int) -> None:
        i = start + 1
        depth = 1
        while depth:
            if tokens[i].matches(name='OP', src='{'):
                depth += 1
            elif tokens[i].matches(name='OP', src='}'):
                depth -= 1
            i += 1

        for i in range(i + 1, len(tokens)):
            if tokens[i].name in NON_CODING_TOKENS:
                continue
            elif tokens[i].matches(name='OP', src='='):
                break
            else:
                return  # not an unpacking assignment

        equals = i

        for i in range(i + 1, len(tokens)):
            if tokens[i].name != UNIMPORTANT_WS:
                break

        for i in range(i + 1, len(tokens)):
            if tokens[i].name == 'NEWLINE':
                break
        else:
            raise AssertionError('unreachable')

        to_replace.append((start, equals, i))

    for i, token in enumerate(tokens):
        if seen_newline:
            if token.name in NON_CODING_TOKENS:
                continue
            elif token.name == 'OP' and token.src == '{':
                _maybe_unpacking(i)
                seen_newline = False
        elif token.name == 'NEWLINE':
            seen_newline = True

    for start, equals, end in reversed(to_replace):
        tokens[start:end] = _make_match(tokens, start, equals, end)
    return tokens_to_src(tokens), length


class IncrementalDecoder(codecs.BufferedIncrementalDecoder):
    def _buffer_decode(  # pragma: no cover
            self,
            input: Buffer,
            errors: str,
            final: bool,
    ) -> tuple[str, int]:
        if final:
            return decode(input, errors)
        else:
            return '', 0


class StreamReader(utf_8.StreamReader):
    """decode is deferred to support better error messages"""
    _stream = None
    _decoded = False

    @property
    def stream(self) -> _ReadableStream:
        assert self._stream is not None
        if not self._decoded:
            text, _ = decode(self._stream.read())
            self._stream = io.BytesIO(text.encode('UTF-8'))
            self._decoded = True
        return self._stream

    @stream.setter
    def stream(self, stream: _ReadableStream) -> None:
        self._stream = stream
        self._decoded = False

# codec api


codec_map = {
    name: codecs.CodecInfo(
        name=name,
        encode=utf_8.encode,
        decode=decode,
        incrementalencoder=utf_8.IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=utf_8.StreamWriter,
    )
    for name in ('dict-unpacking-at-home', 'dict_unpacking_at_home')
}


def register() -> None:  # pragma: no cover
    codecs.register(codec_map.get)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Prints transformed source.')
    parser.add_argument('filename')
    args = parser.parse_args(argv)

    with open(args.filename, 'rb') as f:
        text, _ = decode(f.read())
    sys.stdout.buffer.write(text.encode())

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

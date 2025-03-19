mom can we have dict unpacking in python?

# we have `dict-unpacking-at-home`

### please don't use this

no seriously.  I do not need [another joke package of mine] to be deemed
"critical" to pypi [^1]

[^1]: with almost a [million downloads per month] and [30M+ total]

[another joke package of mine]: https://pypi.org/p/future-fstrings
[million downloads per month]: https://pypistats.org/packages/future-fstrings
[30M+ total]: https://pepy.tech/projects/future-fstrings

### ok how do I use it

1. `pip install dict-unpacking-at-home`
2. add `# -*- coding: dict-unpacking-at-home -*-` to the top of your file
  (second line if you have a shebang)
3. enjoy!

```python
# -*- coding: dict-unpacking-at-home -*-

dct = {'greeting': 'hello', 'thing': 'world'}

{greeting, thing} = dct
print(greeting, greeting, thing)  # hello hello world

# even with nesting!
dct = {'a': [1, 2, 3]}
{'a': [1, *rest]} = dct
print(rest)  # [2, 3]
```

### problems

the current version breaks line numbers in stacktraces -- the
[correct-line-numbers] branch has a fix.  but [at what cost].

see also [please don't use this](#please-dont-use-this)

[correct-line-numbers]: https://github.com/asottile/dict-unpacking-at-home/tree/correct-line-numbers
[at what cost]: https://github.com/asottile/dict-unpacking-at-home/commit/correct-line-numbers

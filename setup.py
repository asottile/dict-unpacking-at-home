from __future__ import annotations

import os.path

from setuptools import setup
from setuptools.command.install import install as _install


PTH = (
    'try:\n'
    '    import dict_unpacking_at_home\n'
    'except ImportError:\n'
    '    pass\n'
    'else:\n'
    '    dict_unpacking_at_home.register()\n'
)


class install(_install):
    install_lib: str

    def initialize_options(self) -> None:
        _install.initialize_options(self)
        # Use this prefix to get loaded as early as possible
        name = 'aaaaa_' + self.distribution.metadata.name

        contents = f'import sys; exec({PTH!r})\n'
        self.extra_path = (name, contents)

    def finalize_options(self) -> None:
        _install.finalize_options(self)

        install_suffix = os.path.relpath(
            self.install_lib, self.install_libbase,
        )
        if install_suffix == '.':
            pass  # editable
        elif install_suffix == self.extra_path[1]:
            self.install_lib = self.install_libbase
        else:
            raise AssertionError(
                'unexpected install_suffix',
                self.install_lib, self.install_libbase, install_suffix,
            )


setup(cmdclass={'install': install})

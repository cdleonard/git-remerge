from setuptools import setup

setup(
        command_options=dict(
            build_sphinx=dict(
                source_dir = ('setup.py', 'doc/sphinx-source'),
                build_dir = ('setup.py', 'doc/sphinx-output'),
            ),
        ),
)

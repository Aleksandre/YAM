

from distutils.core import setup

setup(
    name = 'yamc',
    packages = ['yam','art'],
    version = '0.0.1',
    description = 'Yet another media center.',
    author='Aleksandre Clavet',
    url='https://github.com/Aleksandre/YAM',
    license='LICENSE.txt',
    install_requires=[
        "Python >= 2.7",
        "python-mutagen",
    ]
)
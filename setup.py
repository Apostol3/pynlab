from setuptools import setup, find_packages

setup(
    name='pynlab',
    version='0.2.0',
    packages=find_packages(),
    install_requires=['pywin32>=219'],
    license='MIT',
    author='Kirill Dudkin',
    author_email='apostol3.mv@yandex.ru',
    description='nlab for python'
)

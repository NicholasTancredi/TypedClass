from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='TypedClass',
    version='0.0.3',
    description='Extend other classes to give them type checking via annotations',
    url='https://github.com/w0251251/TypedClass',
    author='Nicholas Tancredi',
    author_email='nicholastancredi@gmail.com',
    license='GNU',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
)
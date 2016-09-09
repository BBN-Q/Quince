from setuptools import setup

setup(
    name='quince',
    version='0.1',
    author='Quince Developers',
    # package_dir={'':'quince'},
    packages=['quince'],
    scripts=["run-quince.py"],
    data_files=["assets"],
    description='Quince is a node centric experience.',
    long_description=open('README.md').read(),
    install_requires=[
        "Numpy >= 1.6.1",
    ]
)
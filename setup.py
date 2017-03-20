from setuptools import setup
import os

if os.name == 'nt':
    # Find the path
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "run-quince.py")

    # Create the run-quince.bat script
    with open('run-quince.bat', 'w') as f:
        f.write("python {} %*\n".format(path))

    script_names = ['run-quince.bat']
else:
    script_names = ['run-quince.py']

setup(
    name='quince',
    version='0.1',
    author='Quince Developers',
    # package_dir={'':'quince'},
    packages=['quince'],
    scripts=script_names,
    data_files=["assets"],
    description='Quince is a node centric experience.',
    long_description=open('README.md').read(),
    install_requires=[
        "Numpy >= 1.6.1",
        "QtPy >= 1.1.2"
    ]
)

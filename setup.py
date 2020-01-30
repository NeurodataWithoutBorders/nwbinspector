from setuptools import setup, find_packages

# Get the long description from the README file
with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='nwbinspector',
    version='0.1.0',
    description='tool to inspect NWB files for best practices compliance',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Ryan Ly, Ben Dichter',
    author_email='rly@lbl.gov, ben.dichter@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'pynwb'
    ],
    entry_points={
        'console_scripts': [
            'nwbinspector=nwbinspector:main'
        ]
    }
)

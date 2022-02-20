import os

from setuptools import setup

from version import version_info

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Information Technology',
    'Operating System :: OS Independent',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.9',
    'Topic :: Internet :: WWW/HTTP :: HTTP Servers'
]


def read(name: str) -> str:
    """https://pythonhosted.org/an_example_pypi_project/setuptools.html#setting-up-setup-py - reference."""
    return open(os.path.join(os.path.dirname(__file__), name)).read()


setup(
    name='fileware',
    version='.'.join(str(c) for c in version_info),
    description='Python module to, serve files in physical memory to localhost and tunnel to a public endpoint.',
    long_description=read('README.md') + '\n\n' + read('CHANGELOG'),
    long_description_content_type='text/markdown',
    url='https://github.com/thevickypedia/fileware',
    author='Vignesh Sivanandha Rao',
    author_email='svignesh1793@gmail.com',
    License='MIT',
    classifiers=classifiers,
    keywords='personal-cloud, file-server, ssl',
    packages=['.fileware'],
    python_requires=">=3.8",
    include_package_data=True,
    install_requires=read(name='requirements.txt').splitlines(),
    project_urls={
        'Docs': 'https://thevickypedia.github.io/fileware',
        'Bug Tracker': 'https://github.com/thevickypedia/fileware/issues'
    }
)

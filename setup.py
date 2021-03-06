from setuptools import setup
import versioneer

requirements = [
    # package requirements go here
]

setup(
    name='openff-spellbook',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Handy functionality for working with OpenFF data",
    license="MIT",
    author="Trevor Gokey",
    author_email='tgokey@uci.edu',
    url='https://github.com/trevorgokey/openff-spellbook',
    packages=['offsb',
              'offsb/op',
              'offsb/tools',
              'offsb/search',
              'offsb/qcarchive',
              'offsb/rdutil',
              'treedi'],
    
    install_requires=requirements,
    keywords='openff-spellbook',
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)

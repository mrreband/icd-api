from setuptools import setup

install_requires = [
    'python-dotenv>=0.21.0',
    'requests>=2.28.1',
    'requests_cache>=1.2.0'
]

tests_require = [
    'pytest>=5.1.2',
]

setup(
    name='icd-api',
    version="0.0.13",
    description='',
    url='https://github.com/mrreband/icd-api',
    packages=['icd_api'],
    install_requires=install_requires,
    tests_require=tests_require,
    zip_safe=False,
)

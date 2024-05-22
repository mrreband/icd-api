from setuptools import setup

install_requires = [
    'python-dotenv',
    'requests',
]

tests_require = [
    'pytest>=5.1.2',
]

setup(
    name='icd-api',
    version="0.0.9",
    description='',
    url='https://github.com/mrreband/icd-api',
    packages=['icd_api'],
    install_requires=install_requires,
    tests_require=tests_require,
    zip_safe=False,
)

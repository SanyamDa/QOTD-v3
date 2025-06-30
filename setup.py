from setuptools import setup, find_packages

setup(
    name="quote_bot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'python-telegram-bot>=20.0',
        'python-dotenv>=0.19.0',
        'apscheduler>=3.9.0',
        'pytz>=2021.3',
        'openai>=1.0.0'
    ],
    python_requires='>=3.8',
)

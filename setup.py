from setuptools import setup, find_packages


version = '0.0.3'
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='loggerflow',
    version=version,
    packages=find_packages(),
    url='https://github.com/DeNRuDi/loggerflow',
    author='DeNRuDi',
    author_email='denisrudnitskiy0@gmail.com',
    description='A new level of bug tracking for your Python projects',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'requests',
        'discordwebhook',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
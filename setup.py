from setuptools import setup, find_packages


version = '0.0.5'
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()
    long_description = long_description.replace('![StartImage](show.png)', '')

setup(
    name='loggerflow',
    version=version,
    packages=find_packages(),
    url='https://github.com/DeNRuDi/loggerflow',
    author='DeNRuDi',
    include_package_data=True,
    author_email='denisrudnitskiy0@gmail.com',
    description='A new level of bug tracking for your Python projects',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'requests',
        'discordwebhook',
        'fastapi',
        'aiohttp',
        'aiofiles',
        'uvicorn',
        'jinja2',
        'aiosqlite',
        'sqlalchemy',
        'psutil',
        'pydantic-settings',
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
        'Programming Language :: Python :: 3.11',
    ],
    entry_points={
        'console_scripts': [
            'loggerflow = loggerflow.lifecycle.lifecycle_server:run_loggerflow_server',
        ],
    }
)

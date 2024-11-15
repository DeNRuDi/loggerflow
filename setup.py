from setuptools import setup, find_packages


version = '0.0.6'
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()
    long_description = long_description.replace(
        '![StartImage](photos/loggerflow.png)', ''
    ).replace(
        '![StartImage](photos/project_metrics.png)', ''
    )


setup(
    name='loggerflow',
    version=version,
    packages=find_packages(),
    url='https://github.com/DeNRuDi/loggerflow',
    author='DeNRuDi',
    include_package_data=True,
    author_email='denisrudnitskiy0@gmail.com',
    description='Simple and fast solution of bug tracking for your Python projects and backlight project lines in traceback.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'requests',
        'discordwebhook',
        'fastapi',
        'aiohttp',
        'aiofiles',
        'uvicorn[standard]',
        'jinja2',
        'aiosqlite',
        'sqlalchemy',
        'psutil',
        'pydantic-settings',
        'python-multipart',
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
        'Programming Language :: Python :: 3.12',
    ],
    entry_points={
        'console_scripts': [
            'loggerflow = loggerflow.lifecycle.lifecycle_server:run_loggerflow_server',
        ],
    }
)

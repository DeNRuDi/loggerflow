## LoggerFlow
```
  \     \
  _\_____\
 | |   __  \___       /     __     __    __   ___   ___   ----         __
 | |  |__/     |     /    /   /  / __  / __  /__   /  /  /___  /     /   /   /  /  /
 | |      ____/     /___ /___/  /___/ /___/ /___  /     /     /___  /___/   /__/__/
 |_|_____/
```

A new level of bug tracking for your Python projects.

<details>
  <summary>Changes (0.0.4 - actual)</summary>
  
 - v. 0.0.4
    - improved stacktrace cleaning for `traceback='clean'`;
    - template for tracking the status of projects (will be added in v. 0.0.5);
    - rename method `exclude_sending_filter` to `exclude`;
    - added method `send_traceback_to_backend` for manual sending of traceback to the backend;
    - changes in project architecture.

  - v. 0.0.3
    - added the `traceback='full'` attribute to the LoggerFlow constructor, which allows you to send full, clean or minimal traceback to the backend (depending on your preferences).
    You can pass 3 parameters:
        - `full` -  Sending full traceback on your backend/backends;
        - `clean` - Sending your program's stacktrace (clearing lines that were are called from libraries);
        - `minimal` - Sending a 1 line with name file, number line and last line of your traceback;
    - minor fixes in project architecture;
    - writing documentation for project.
  - v. 0.0.2
    - added logging in threads (to disable logging in threads - pass the parameter thread_logging=False to the LoggerFlow constructor);
    - minor fixes;
  - v. 0.0.1 
    - create project LoggerFlow;
</details>

<h5> Simple start (with Telegram backend): </h5>

```
from loggerflow.backends.telegram import TelegramBackend
from loggerflow import LoggerFlow


backend = TelegramBackend(
    token='telegram_token',
    chat_id=-123456789,
    authors=['@DeNRuDi', ]
)

lf = LoggerFlow(project_name='Test', backend=backend)
lf.run()

raise Exception('Test Error')
```

<h5> Example with multiple backends: </h5>

```
from loggerflow.backends.telegram import TelegramBackend
from loggerflow.backends.discord import DiscordBackend
from loggerflow import LoggerFlow

backend_telegram = TelegramBackend(
    token='bot_token',
    chat_id=-1234567890,
    authors=['@telegram_username', ]
)

backend_discord = DiscordBackend(
    webhook_url='webhook_url',
    authors=['@discord_username', ]
)

lf = LoggerFlow(project_name='Test', backend=[backend_telegram, backend_discord])
lf.run()

raise Exception('Test Error')
```

<h5> Exclude traceback which should not be sent: </h5>

```
lf = LoggerFlow(project_name='Test', backend=backend)
lf.exclude('ValueError')
lf.exclude('502 Bad Gateway')
lf.run()
```

<h5>Simple integrations with frameworks</h5>
<details>
    <summary>Django</summary>

File `settings.py`:
```
import os
from pathlib import Path

from loggerflow.backends.file import FileBackend
from loggerflow import LoggerFlow

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']


lf = LoggerFlow(project_name='Test', backend=FileBackend('test.log'), traceback='clean')
lf.run()
```
</details>


<details>
    <summary>FastAPI</summary>

`FastAPI` already contains an automatic excepthook-handler, so errors must be sent
using the `lf.send_data(your_data)` method.

Example:
```
from loggerflow.backends.file import FileBackend
from loggerflow import LoggerFlow

from fastapi.responses import JSONResponse
from fastapi import FastAPI

import traceback
import uvicorn

app = FastAPI()
lf = LoggerFlow(project_name='Test', backend=FileBackend(file='test.log'), traceback='clean')
lf.run()


@app.get('/')
async def index():
    return {"status": 200}


@app.exception_handler(Exception)
async def exception_handler(request, exc):
    lf.send_data_to_backend(traceback.format_exc())
    return JSONResponse({'status': 500})


if __name__ == '__main__':
    uvicorn.run(app=app)
```
</details>







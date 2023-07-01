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


<h5> Simple start (with Telegram backend): </h5>
<details>
  <summary>Changes (0.0.3 - actual)</summary>

  - v.0.0.3
    - added the `traceback='full'` attribute to the LoggerFlow constructor, which allows you to send full, clean or minimal traceback to the backend (depending on your preferences).
    You can pass 3 parameters:
        - `full` -  Sending full traceback on your backend/backends;
        - `clean` - Sending your program's stacktrace (clearing lines that were are called from libraries);
        - `minimal` - Sending a 1 line with name file, number line and last line of your traceback;
    - minor fixes in project architecture;
    - writing documentation for project.
  - v.0.0.2
    - added logging in threads (to disable logging in threads - pass the parameter thread_logging=False to the LoggerFlow constructor);
    - minor fixes;
  - v.0.0.1 
    - create project LoggerFlow;
</details>

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
lf.exclude_sending_filter('ValueError')
lf.exclude_sending_filter('502 Bad Gateway')
lf.run()
```





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





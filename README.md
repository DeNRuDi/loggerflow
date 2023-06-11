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

Exclude traceback which should not be sent:
```
lf = LoggerFlow(project_name='Test', backend=backend)
lf.exclude_sending_filter('ValueError')
lf.exclude_sending_filter('502 Bad Gateway')
lf.run()
```





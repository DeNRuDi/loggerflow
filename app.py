from loggerflow.backends.telegram import TelegramBackend
from loggerflow.backends.discord import DiscordBackend
from loggerflow import LoggerFlow

backend_telegram = TelegramBackend(
    token='bot_token',
    chat_id=-1234567890,
    authors=['@telegram_username', ]
)

backend_discord = DiscordBackend(
    webhook_url='https://discord.com/api/webhooks/123456789/token',
    authors=['@discord_username', ]
)

lf = LoggerFlow(project_name='Test', backend=[backend_telegram, backend_discord])
lf.run()

raise Exception('Test Error')


# email - __token__
# password - api token
from loggerflow.backends.file import FileBackend
from loggerflow import LoggerFlow

import asyncio

lf = LoggerFlow(backend=FileBackend(), project_name='Test')
lf.run(loop=asyncio.new_event_loop())


async def main():

    await lf.send_async_data('Test message')
    raise Exception('Test')

asyncio.run(main())

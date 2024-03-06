from loggerflow.lifecycle.routes.websockets import router as websockets_router
from loggerflow.lifecycle.routes.webhooks import router as webhooks_router
from loggerflow.lifecycle.routes.site import site_router

from loggerflow.exceptions import LifecycleException
from loggerflow.lifecycle.database import Database
from fastapi.staticfiles import StaticFiles

from pkg_resources import resource_filename
from fastapi import FastAPI, Depends

import argparse
import asyncio
import uvicorn
import os

from loggerflow.lifecycle.utils.auth import settings, get_authorization

app = FastAPI()
static_files_path = resource_filename('loggerflow.lifecycle', 'static')
app.mount('/static', StaticFiles(directory=static_files_path), name='static')

app.include_router(webhooks_router)
app.include_router(websockets_router)


async def run_server():
    parser = argparse.ArgumentParser(description="Run the LoggerFlow Lifecycle server")
    parser.add_argument('command', choices=['run'], help='Command to run', default='run')
    parser.add_argument('-u', '--host', type=str, default='127.0.0.1', help='Host to run LoggerFlow server')
    parser.add_argument('-p', '--port', type=int, default=8000, help='Port to run LoggerFlow server')
    parser.add_argument('-d', '--database', type=str, default='sqlite+aiosqlite:///loggerflow.db',
                        help='SQLAlchemy database connection string, default is "sqlite+aiosqlite:///loggerflow.db"')
    parser.add_argument('-a', '--auth', type=str, help='Auth credentials in format login:password', required=False)
    parser.add_argument('--disable-log',  action='store_true', help='Disable uvicorn log in terminal')

    args = parser.parse_args()
    if 'sqlite://' in args.database:
        db_name = args.database.split('///')[-1]
        database_path = 'sqlite+aiosqlite:///' + os.path.join(os.getcwd(), db_name)
    else:
        database_path = args.database

    database = Database(database_path)
    await database.init()

    if args.auth:
        if ':' not in args.auth:
            raise LifecycleException('Your credentials is not correct. Correct format is login:password')
        creds = args.auth.split(':', maxsplit=1)
        settings.username = creds[0]
        settings.password = creds[1]
        app.include_router(site_router, dependencies=[Depends(get_authorization)])

    app.include_router(site_router)

    config = uvicorn.Config(app, host=args.host, port=args.port, loop="asyncio", access_log=not args.disable_log)
    server = uvicorn.Server(config)
    await server.serve()


def run_loggerflow_server():
    asyncio.run(run_server())


if __name__ == '__main__':
    run_loggerflow_server()

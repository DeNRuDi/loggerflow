from loggerflow.lifecycle.routes.websockets import router as websockets_router
from loggerflow.lifecycle.routes.webhooks import router as webhooks_router
from loggerflow.lifecycle.routes.site import router as site_router
from loggerflow.lifecycle.utils.auth import settings, get_authorization

from loggerflow.exceptions import LifecycleException, NotCorrectAlarmException
from loggerflow.backends.abstract_backend import AbstractAlarmBackend
from loggerflow.lifecycle.database import Database
from loggerflow.utils.filters import AlarmFilter
from loggerflow.backends import AlarmBackend
from fastapi.staticfiles import StaticFiles

from pkg_resources import resource_filename
from fastapi import FastAPI, Depends

import importlib
import argparse
import asyncio
import uvicorn
import os


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
    parser.add_argument('-c', '--custom-alarm',  type=str,
                        help='single class or comma-separated list of custom alarm classes (e.g., "name_of_file.CustomAlarmBackend,test.AnotherAlarm")')

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
    else:
        app.include_router(site_router)

    custom_alarm_instances = []
    if args.custom_alarm:
        alarm_classes = map(str.strip, args.custom_alarm.split(','))
        for alarm in alarm_classes:
            if '.' in alarm:
                module_name, class_name = alarm.rsplit('.', 1)
                module = importlib.import_module(module_name)
                alarm_class = getattr(module, class_name)

                if not issubclass(alarm_class, AbstractAlarmBackend):
                    raise NotCorrectAlarmException(f'{class_name} does not inherit from AbstractAlarmBackend')

                if hasattr(alarm_class, 'alarm_required_fields'):
                    if not isinstance(alarm_class.alarm_required_fields, (list, tuple)):
                        raise NotCorrectAlarmException('Alarm display info must be a list or tuple')
                    if len(alarm_class.alarm_required_fields) == 0:
                        raise NotCorrectAlarmException('Alarm display info does not contain any alarm fields.')

                    custom_alarm_instances.append(alarm_class)
                else:
                    raise NotCorrectAlarmException('Alarm class does not contain properties "alarm_required_fields"')
            else:
                raise NotCorrectAlarmException('Alarm class was not transmitted correctly')

    AlarmBackend.extend(custom_alarm_instances)
    filter_cls = {cls.__name__: cls for cls in AlarmBackend}
    AlarmFilter.filters.update(**filter_cls)

    config = uvicorn.Config(app, host=args.host, port=args.port, loop="asyncio", access_log=not args.disable_log)
    server = uvicorn.Server(config)
    await server.serve()


def run_loggerflow_server():
    asyncio.run(run_server())


if __name__ == '__main__':
    run_loggerflow_server()

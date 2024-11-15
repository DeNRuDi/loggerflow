import asyncio
from datetime import datetime, timedelta

from loggerflow.lifecycle.database.queries import LifecycleQuery, AlarmerQuery
from loggerflow.lifecycle.database.models import Status, Event
from loggerflow.lifecycle.lifecycle_cli import logger
from loggerflow.utils.filters import AlarmFilter
from loggerflow.backends import FileBackend


class AlarmListener:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.project_tasks = {}
        return cls._instance

    async def start_all_project_listeners(self, projects):

        for project in projects:
            if project.get('status') == 'ONLINE' and project.get('connected_alarm_ids'):
                logger.info(f'Run alarm listener for project {project["project_name"]}')
                await self.start_project_listener(project['id'], project['project_name'])

    async def shutdown_all_project_listeners(self, projects):
        for project in projects:
            if project.get('connected_alarm_ids'):
                logger.info(f'Stop alarm listener for project {project["project_name"]}')
                await self.stop_project_listener(project['id'], project['project_name'])

    async def start_project_listener(self, project_id: int, project_name: str):
        if project_id in self.project_tasks:
            return

        project_alarms = await AlarmerQuery.get_alarms(project_id)
        if project_alarms:
            task = asyncio.create_task(self._monitor_project(project_id))
            task.add_done_callback(self._handle_task_result_if_found)
            self.project_tasks[project_id] = {'task': task, 'sent_alarm': False}
            logger.info(f"Alarm task monitoring started for project {project_name}")

    async def stop_project_listener(self, project_id: int, project_name: str, message: str = None):
        task_data = self.project_tasks.pop(project_id, None)
        if task_data and task_data.get('task'):
            if message:
                await AlarmerQuery.save_alarm_event(
                    project_id=project_id, alarm_id=None, event_type=Event.shutdown, message=message
                )

            task = task_data.get('task')
            task.cancel()
            logger.info(f"Alarm task monitoring stopped for project {project_name}")

    @staticmethod
    def _handle_task_result_if_found(task: asyncio.Task):
        try:
            task.result()
        except asyncio.CancelledError:
            ...
        except Exception as e:
            logger.error(f"Alarm task failed with error: {e}")

    @staticmethod
    async def _send_alarm(project, message, event: Event = Event.shutdown.value):
        project_alarms = await AlarmerQuery.get_alarms(project.id)
        for alarm in project_alarms:
            try:
                alarm_instance = AlarmFilter.filters[alarm.backend_type](**alarm.config_data)
                if isinstance(alarm_instance, FileBackend):
                    message_with_time = f'{message}; time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                    await alarm_instance.async_write_flow(text=message_with_time, project_name=project.project_name)
                else:
                    await alarm_instance.async_write_flow(text=message, project_name=project.project_name)

                await AlarmerQuery.save_alarm_event(project_id=project.id, alarm_id=alarm.id, event_type=event, message=message)
                logger.info(f'Sent alarm ({event}) for project {project.project_name} to {alarm.alarmer_name}')
            except Exception:
                await AlarmerQuery.save_alarm_event(
                    project_id=project.id, alarm_id=alarm.id, event_type=event, message='Failed to send message in this alarmer'
                )
                logger.error(f'Failed to send alarm ({event}) for project {project.project_name} to {alarm.alarmer_name}')


    async def _monitor_project(self, project_id: int):
        await AlarmerQuery.save_alarm_event(
            project_id=project_id, alarm_id=None, event_type=Event.startup,
            message='Start alarmer for project'
        )
        while True:
            project = await LifecycleQuery.get_project(project_id)
            now = datetime.now()
            if project:
                if (project.last_heartbeat < now - timedelta(seconds=project.heartbeat + 2) and
                    not self.project_tasks[project_id]['sent_alarm']):
                    await self._send_alarm(
                        project,
                        message=f'Project has been shutdown',
                        event=Event.shutdown
                    )
                    self.project_tasks[project_id]['sent_alarm'] = True

                elif self.project_tasks[project_id]['sent_alarm'] and project.status == Status.online:
                    await self._send_alarm(
                        project,
                        message=f'Project has been startup',
                        event=Event.startup
                    )
                    self.project_tasks[project_id]['sent_alarm'] = False

                await asyncio.sleep(project.heartbeat)
            else:
                # project was deleted
                await self.stop_project_listener(project_id, f'id({project_id})')

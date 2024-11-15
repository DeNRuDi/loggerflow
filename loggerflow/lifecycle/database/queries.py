from loggerflow.lifecycle.database.models import (
    Project, ProjectException, Status, LFSettings, Alarmer, Metric, AlarmEvent, Event
)
from loggerflow.utils.stack_cleaner import StackCleaner
from loggerflow.lifecycle.database import Database

from datetime import datetime, timedelta
from typing import List, Union

from sqlalchemy import func, desc, delete, text
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.future import select

db = Database()


class AlarmerQuery:
    @staticmethod
    async def save_alarmer(config_data: dict):
        async with db.session() as session:
            backend_type = config_data.pop('backend_type')
            alarmer_name = config_data.pop('alarmer_name')
            alarmer = Alarmer(alarmer_name=alarmer_name, backend_type=backend_type, config_data=config_data)
            session.add(alarmer)
            await session.commit()
            await session.refresh(alarmer)
            return alarmer.to_dict()

    @staticmethod
    async def save_alarm_event(project_id: int, alarm_id: Union[int, None], event_type: Event,
                               event_time: datetime = None, message: str = None):
        async with db.session() as session:
            alarm_event = AlarmEvent(
                project_id=project_id,
                alarm_id=alarm_id,
                event_type=event_type,
                event_time=event_time,
                message=message
            )
            session.add(alarm_event)
            await session.commit()

    @staticmethod
    async def get_alarms(project_id: int = None) -> list:
        async with db.session() as session:
            if project_id:
                stmt = await session.execute(
                    select(Project).where(Project.id == project_id).options(selectinload(Project.connected_alarms))
                )
                project = stmt.scalar_one_or_none()
                if not project:
                    return []
                alarms = project.connected_alarms
            else:
                stmt = await session.execute(select(Alarmer))
                alarms = stmt.scalars().all()

            return alarms

    @staticmethod
    async def get_alarm_events(page: int, page_size: int):
        async with db.session() as session:
            offset = (page - 1) * page_size
            query = (
                select(AlarmEvent)
                .order_by(desc(AlarmEvent.event_time))
                .options(
                    joinedload(AlarmEvent.project),
                    joinedload(AlarmEvent.alarm)
                )
                .offset(offset)
                .limit(page_size)
            )
            result = await session.execute(query)
            alarm_events = result.scalars().all()

            total_query = select(func.count(AlarmEvent.id))
            total_events = (await session.execute(total_query)).scalar()

            return alarm_events, total_events

    @staticmethod
    async def delete_alarmer(alarmer_id: int):
        async with db.session() as session:
            if session.bind.dialect.name == "sqlite":
                await session.execute(text("PRAGMA foreign_keys=ON"))

            await session.execute(
                delete(Alarmer).where(Alarmer.id == alarmer_id)
            )
            await session.commit()

    @staticmethod
    async def connect_alarms_to_project(project_id: int, alarm_ids: List[int]) -> bool:
        async with db.session() as session:
            result = await session.execute(
                select(Project).where(Project.id == project_id).options(selectinload(Project.connected_alarms))
            )
            project = result.scalar_one()
            existing_alarm_ids = {int(alarm.id) for alarm in project.connected_alarms}
            new_alarm_ids = set(alarm_ids)

            # for extend
            alarms_to_add = new_alarm_ids - existing_alarm_ids
            if alarms_to_add:
                new_alarms = await session.execute(select(Alarmer).where(Alarmer.id.in_(alarms_to_add)))
                new_alarms = new_alarms.scalars().all()
                project.connected_alarms.extend(new_alarms)
            # for remove
            alarms_to_remove = existing_alarm_ids - new_alarm_ids
            if alarms_to_remove:
                alarms_to_remove = [alarm for alarm in project.connected_alarms if alarm.id in alarms_to_remove]
                for alarm in alarms_to_remove:
                    project.connected_alarms.remove(alarm)

            await session.commit()
            return project.connected_alarms

    @staticmethod
    async def delete_all_alarm_events():
        async with db.session() as session:
            await session.execute(
                delete(AlarmEvent)
            )
            await session.commit()


class SettingsQuery:

    @staticmethod
    async def change_lf_settings(new_settings: dict):
        async with db.session() as session:
            result = await session.execute(select(LFSettings))
            settings = result.scalars().first()
            if not settings:
                settings = LFSettings(**new_settings)
                session.add(settings)
            else:
                settings.update_from_dict(new_settings)
            await session.commit()

    @staticmethod
    async def get_lf_settings():
        async with db.session() as session:
            result = await session.execute(select(LFSettings))
            settings = result.scalars().first()
            return settings


class MetricQuery:

    @staticmethod
    async def create_metric(heartbeat_info: dict):
        async with db.session() as session:
            result = await session.execute(
                select(Project).where(Project.project_name == str(heartbeat_info['project_name']))
            )

            project = result.scalar_one()
            metrics = heartbeat_info.get('last_readings')

            metric = Metric(
                project_id=project.id,
                data={
                    "cpu": float(metrics['cpu']),
                    "used_memory": float(metrics['used_memory']),
                    "total_memory": float(metrics['total_memory']),
                    "process_memory": float(metrics['process_memory']),
                    "availability": 1 if project.status == Status.online else 0
                },
                last_heartbeat=datetime.now()
            )
            session.add(metric)
            await session.commit()


    @staticmethod
    async def get_metrics(project_id: int, filter_time: int):
        async with db.session() as session:
            filter_duration = timedelta(minutes=filter_time)
            start_time = datetime.now() - filter_duration

            stmt = await session.execute(
                select(Metric)
                .where(Metric.project_id == project_id, Metric.last_heartbeat >= start_time)
                .order_by(Metric.last_heartbeat.asc())
            )
            metrics = stmt.scalars().all()
            return metrics

    @staticmethod
    async def delete_old_metrics():
        async with db.session() as session:
            threshold_date = datetime.now() - timedelta(days=7)
            await session.execute(
                delete(Metric).where(Metric.last_heartbeat < threshold_date)
            )
            await session.commit()

    @staticmethod
    async def delete_metrics(project_id: int):
        async with db.session() as session:
            await session.execute(
                delete(Metric).where(Metric.project_id == project_id)
            )
            await session.commit()

class LifecycleQuery:

    @staticmethod
    async def add_project_exception(project_exception: dict):

        async with db.session() as session:
            result = await session.execute(
                select(Project).where(Project.project_name == str(project_exception['project_name']))
            )
            project = result.scalar_one()
            pe = ProjectException(
                project_id=project.id,
                traceback=project_exception['traceback']
            )
            session.add(pe)
            await session.commit()

    @staticmethod
    async def create_or_update_project(backend_info: dict):
        backend_info.update({'last_heartbeat': datetime.now()})
        async with db.session() as session:
            stmt = await session.execute(select(Project).where(Project.project_name == str(backend_info['project_name'])))
            project = stmt.scalars().first()
            if not project:
                project = Project(
                    project_name=backend_info['project_name'],
                    connected_backends=backend_info['connected_backends'],
                    last_readings=backend_info['last_readings'],
                    implementation=backend_info['implementation'],
                    heartbeat=backend_info['heartbeat'],
                    status=Status.online,
                )
                session.add(project)
                await session.commit()
            else:
                if not project.hidden:
                    if project.update_from_dict(backend_info):
                        await session.commit()

    @staticmethod
    async def set_hide_in_project(project_id: int, hidden: bool = True):
        async with db.session() as session:
            stmt = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = stmt.scalar_one()
            project.hidden = hidden
            await session.commit()

    @staticmethod
    async def get_all_projects(hidden: bool = False):
        async with db.session() as session:
            stmt = await session.execute(
                select(Project, func.count(ProjectException.id).label('exceptions_count'))
                .filter(Project.hidden == hidden)
                .outerjoin(ProjectException, Project.id == ProjectException.project_id)
                .group_by(Project.id)
                .options(selectinload(Project.connected_alarms))
            )
            projects_with_exceptions = stmt.all()
            projects = []
            total_info = {
                'project_name': f'Total ({len(projects_with_exceptions)})',
                'exceptions_count': 0,
                'status': 'TOTAL',
                'connected_backend': '',
                'traceback': ''
            }

            for project, exceptions_count in projects_with_exceptions:
                project.exceptions_count = exceptions_count
                project_dict = project.to_dict()
                project_dict.update({'connected_alarm_ids': [int(alarm.id) for alarm in project.connected_alarms]})
                projects.append(project_dict)
                total_info.update({'exceptions_count': total_info['exceptions_count'] + exceptions_count})
                await LifecycleQuery.check_status(session, project)

        return projects, total_info

    @staticmethod
    async def get_real_projects_heartbeat(project_id: int = None):
        async with db.session() as session:
            heartbeat_info = []
            if project_id:
                stmt = await session.execute(select(Project).where(Project.id == project_id))
                projects = [stmt.scalar_one()]
            else:
                stmt = await session.execute(select(Project))
                projects = stmt.scalars().all()

            for proj in projects:
                await LifecycleQuery.check_status(session, proj)

                heartbeat_info.append({
                    'project_id': proj.id,
                    'project_name': proj.project_name,
                    'status': proj.status,
                    'last_heartbeat': proj.last_heartbeat.strftime('%Y-%m-%d %H:%M:%S'),
                    'last_readings': proj.last_readings,
                    'hidden': proj.hidden,
                })

            await session.commit()
            return heartbeat_info

    @staticmethod
    async def get_exceptions_info_from_project(project_id: int, page: int, page_size: int) -> tuple:
        async with db.session() as session:
            sc = StackCleaner()
            stmt = select(ProjectException).where(
                ProjectException.project_id == project_id
            ).order_by(desc(ProjectException.error_date))
            result = await session.execute(stmt)
            total_exceptions = result.scalars().all()

            stmt_paginated = stmt.offset((page - 1) * page_size).limit(page_size)
            result_paginated = await session.execute(stmt_paginated)
            paginated_exceptions = result_paginated.scalars().all()

            settings = await SettingsQuery.get_lf_settings()
            exceptions = []
            for info in paginated_exceptions:
                exception_data = info.to_dict()
                clean_traceback = sc.clean_traceback(exception_data['traceback'])
                if exception_data['traceback'] != clean_traceback:
                    exception_data.update({'clean_traceback': clean_traceback})
                    exception_data.update({'header_traceback': sc.clean_traceback(exception_data['traceback'], minimal=True)})

                    if settings.backlight_traceback:
                        exception_data['traceback'] = sc.format_traceback_with_backlight(exception_data['traceback'], format_type='html')
                    exceptions.append(exception_data)

            stmt_project = select(Project).where(Project.id == project_id)
            project_result = await session.execute(stmt_project)
            project = project_result.scalar_one()

            return project.project_name, exceptions, len(total_exceptions)

    @staticmethod
    async def update_heartbeat(heartbeat_info: dict):
        now = datetime.now()
        async with db.session() as session:
            stmt = await session.execute(
                select(Project).where(Project.project_name == str(heartbeat_info['project_name']))
            )
            project = stmt.scalar_one()
            project.last_heartbeat = now
            project.last_readings = heartbeat_info['last_readings']
            if project.status == Status.offline:
                project.status = Status.online

            await session.commit()

    @staticmethod
    async def delete_exception(exception_id: int):
        async with db.session() as session:
            await session.execute(
                delete(ProjectException).where(ProjectException.id == exception_id)
            )
            await session.commit()

    @staticmethod
    async def delete_project(project_id: int):
        async with db.session() as session:
            if session.bind.dialect.name == "sqlite":
                await session.execute(text("PRAGMA foreign_keys=ON"))
            project = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = project.scalar_one()
            await session.delete(project)
            await session.commit()

    @staticmethod
    async def set_project_status(project_name: str, status: Status):
        async with db.session() as session:
            project = await session.execute(
                select(Project).where(Project.project_name == project_name)
            )
            project = project.scalar_one()
            project.status = status
            session.add(project)
            await session.commit()


    @staticmethod
    async def get_project(project_id: int) -> Project:
        async with db.session() as session:
            project = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = project.scalar_one_or_none()
            if project:
                await LifecycleQuery.check_status(session, project)
        return project

    @staticmethod
    async def get_project_by_name(project_name: str) -> Project:
        async with db.session() as session:
            project = await session.execute(
                select(Project).where(Project.project_name == project_name)
            )
            project = project.scalar_one_or_none()
            if project:
                await LifecycleQuery.check_status(session, project)
        return project

    @staticmethod
    async def check_status(session, project):
        now = datetime.now()
        if project.heartbeat:
            if project.last_heartbeat + timedelta(seconds=project.heartbeat + 2) > now:
                project.status = Status.online
            else:
                project.status = Status.offline
        await session.commit()

from loggerflow.lifecycle.database.models import Project, ProjectException, Status
from loggerflow.lifecycle.database import Database
from loggerflow.utils.stack_cleaner import StackCleaner

from datetime import datetime, timedelta

from sqlalchemy import func, desc, delete
from sqlalchemy.future import select

db = Database()


class LifecycleQuery:
    # bug in static linter with db.session(Parameter '_P' unfilled), but code is correct with @asynccontextmanager

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
                projects.append(project.to_dict())
                total_info.update({'exceptions_count': total_info['exceptions_count'] + exceptions_count})

        return projects, total_info

    @staticmethod
    async def get_real_projects_heartbeat():
        async with db.session() as session:
            heartbeat_info = []
            stmt = await session.execute(select(Project))
            projects = stmt.scalars().all()

            now = datetime.now()
            for proj in projects:
                if proj.heartbeat:
                    if proj.last_heartbeat + timedelta(seconds=proj.heartbeat) > now:
                        proj.status = Status.online
                    else:
                        proj.status = Status.offline

                heartbeat_info.append({
                    'project_id': proj.id,
                    'project_name': proj.project_name,
                    'status': proj.status,
                    'last_heartbeat': proj.last_heartbeat.strftime('%Y-%m-%d %H:%M:%S'),
                    'last_readings': proj.last_readings,
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

            exceptions = []
            for info in paginated_exceptions:
                exception_data = info.to_dict()
                clean_traceback = sc.clean_traceback(exception_data['traceback'])
                if exception_data['traceback'] != clean_traceback:
                    exception_data.update({'clean_traceback': clean_traceback})
                    exception_data.update({'header_traceback': sc.clean_traceback(exception_data['traceback'], minimal=True)})
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

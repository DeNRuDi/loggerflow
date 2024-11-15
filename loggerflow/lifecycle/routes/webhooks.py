from fastapi import Request, APIRouter


from loggerflow.lifecycle.database.queries import LifecycleQuery, MetricQuery
from loggerflow.lifecycle.utils.alarm_listener import AlarmListener

router = APIRouter(prefix='/loggerflow')


@router.post('/heartbeat')
async def heartbeat(request: Request):
    heartbeat_info = await request.json()
    await LifecycleQuery.update_heartbeat(heartbeat_info)
    await MetricQuery.create_metric(heartbeat_info)
    project = await LifecycleQuery.get_project_by_name(heartbeat_info['project_name'])

    if not project.hidden:
        al = AlarmListener()
        await al.start_project_listener(project.id, project_name=project.project_name)
    return {'status': 200}


@router.post('/handshake')
async def handshake(request: Request):
    backend_info = await request.json()
    await LifecycleQuery.create_or_update_project(backend_info)
    return {'status': 200}


@router.post('/project_error')
async def project_error(request: Request):
    project_exception = await request.json()
    await LifecycleQuery.add_project_exception(project_exception)
    return {'status': 200}

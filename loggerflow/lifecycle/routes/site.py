from loggerflow.lifecycle.database.models import Status
from loggerflow.lifecycle.database.queries import LifecycleQuery, AlarmerQuery, SettingsQuery, MetricQuery
from loggerflow.lifecycle.database import Database

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request, APIRouter

from pkg_resources import resource_filename

from loggerflow.lifecycle.utils.aggregator import get_aggregation_interval, aggregate_metrics
from loggerflow.lifecycle.utils.alarm_listener import AlarmListener
from loggerflow.utils.filters import AlarmFilter

router = APIRouter()
db = Database()
templates_files_path = resource_filename('loggerflow.lifecycle', 'templates')
templates = Jinja2Templates(directory=templates_files_path)


@router.on_event("startup")
async def startup():
    projects, total = await LifecycleQuery.get_all_projects()

    al = AlarmListener()
    await al.start_all_project_listeners(projects)


@router.on_event("shutdown")
async def shutdown():
    projects, total = await LifecycleQuery.get_all_projects()

    al = AlarmListener()
    await al.shutdown_all_project_listeners(projects)

@router.get('/', response_class=HTMLResponse)
async def start_loggerflow(request: Request):
    projects, total = await LifecycleQuery.get_all_projects()
    settings = await SettingsQuery.get_lf_settings()
    context = {'request': request, 'projects': projects, 'total': total, 'settings': settings}
    return templates.TemplateResponse('loggerflow.html', context)


@router.get('/hidden', response_class=HTMLResponse)
async def hidden(request: Request):
    projects, total = await LifecycleQuery.get_all_projects(hidden=True)
    return templates.TemplateResponse('hidden.html', {'request': request, 'projects': projects})


@router.get('/settings', response_class=HTMLResponse)
async def hidden(request: Request):
    settings = await SettingsQuery.get_lf_settings()
    return templates.TemplateResponse(
        'settings.html',
        {'request': request, 'settings': settings.to_dict()}
    )

###################
# alarmer
@router.get('/alarmer', response_class=HTMLResponse)
async def alarmer(request: Request, page: int = 1, page_size: int = 20):
    alarms = await AlarmerQuery.get_alarms()
    data_alarms = [alarmer.to_dict() for alarmer in alarms]

    alarms_classes = AlarmFilter.filters
    alarm_forms = [{'type': cls.__name__, 'fields': cls.alarm_required_fields} for cls in alarms_classes.values()]

    projects, total_projects = await LifecycleQuery.get_all_projects()
    alarm_events, total_events = await AlarmerQuery.get_alarm_events(page, page_size)
    total_pages = (total_events + page_size - 1) // page_size
    has_next = page < total_pages
    has_previous = page > 1
    al = AlarmListener()

    return templates.TemplateResponse(
        'alarms.html',
        {
            'request': request,
            'alarms': data_alarms,
            'alarm_forms': alarm_forms,
            'projects': projects,
            'alarm_events': alarm_events,
            'page': page,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_previous': has_previous,
            'next_page': page + 1 if has_next else None,
            'previous_page': page - 1 if has_previous else None,
            'working_alarms': al.project_tasks
        }
    )


@router.delete('/delete_alarm_events')
async def delete_alarm_events(request: Request):
    await AlarmerQuery.delete_all_alarm_events()
    return {'success': True}


###################
# metrics

@router.get('/metrics', response_class=HTMLResponse)
async def metrics(request: Request):
    await MetricQuery.delete_old_metrics()
    projects, total = await LifecycleQuery.get_all_projects()
    return templates.TemplateResponse(
        'metrics.html',
        {'request': request, 'projects': projects}
    )


@router.get('/metrics_info/{project_id}')
async def get_metrics(project_id: int, filter_time: int, point_threshold: int = 150):
    metrics = await MetricQuery.get_metrics(project_id, filter_time)
    if len(metrics) <= point_threshold:
        return {
            "timestamps": [metric.last_heartbeat.isoformat() for metric in metrics],
            "cpu": [metric.data["cpu"] for metric in metrics],
            "process_memory": [metric.data["process_memory"] for metric in metrics],
            "used_all_memory": [metric.data["used_memory"] for metric in metrics],
            # "availability": [metric.data["availability"] for metric in metrics],
        }

    interval_seconds = get_aggregation_interval(filter_time)
    interval_minutes = interval_seconds // 60
    grouped_metrics = aggregate_metrics(metrics, interval_seconds, interval_minutes)

    return {
        "timestamps": [metric["timestamp"].isoformat() for metric in grouped_metrics],
        "cpu": [metric["cpu"] for metric in grouped_metrics],
        "process_memory": [metric["process_memory"] for metric in grouped_metrics],
        "used_all_memory": [metric["used_memory"] for metric in grouped_metrics],
        # "availability": [metric["availability"] for metric in grouped_metrics],
    }

@router.delete('/clear_metrics_info/{project_id}')
async def clear_metrics_info(request: Request, project_id: int):
    await MetricQuery.delete_metrics(project_id)
    return {'status': True}


@router.post('/check_alarm')
async def check_alarm(request: Request):
    try:
        alarm_data = await request.json()
        alarm_cls = alarm_data.pop('type', None)
        message = alarm_data.pop('test_message', 'Test Message from LoggerFlow')
        alarmer_name = alarm_data.pop('alarmer_name', '')

        alarm_instance = AlarmFilter.filters[alarm_cls](**alarm_data)
        await alarm_instance.async_write_flow(text=message, project_name=f'Alarmer ({alarmer_name})')
        return {'message': f'Message to {alarm_cls} sent.'}
    except Exception:
        return {'message': 'ERROR for sent'}


@router.delete('/alarms/{alarmer_id}')
async def check_alarm(request: Request, alarmer_id: int):
    await AlarmerQuery.delete_alarmer(alarmer_id)
    return {'success': True, 'alarmer_id': alarmer_id}


@router.post('/connect_alarms_to_project')
async def connect_alarms(request: Request):
    data = await request.json()
    project_id = data['project_id']
    project_name = data['project_name']
    alarm_ids = data['alarm_ids']

    connected_alarms = await AlarmerQuery.connect_alarms_to_project(project_id, list(map(int, alarm_ids)))
    project = await LifecycleQuery.get_project(project_id)

    al = AlarmListener()
    if connected_alarms and project.status == Status.online:
        await al.start_project_listener(project_id, project_name)
    else:
        await al.stop_project_listener(project_id, project_name)

    return {'success': True}

@router.post('/add_alarm')
async def add_alarm(request: Request):
    data = await request.json()
    data.pop('test_message', None)
    alarmer_info = await AlarmerQuery.save_alarmer(data)
    return {"alarm": alarmer_info}

###########


@router.post('/change_settings')
async def hidden(request: Request):
    data = await request.json()
    await SettingsQuery.change_lf_settings(data)


@router.post('/hide_or_return_project')
async def hilde_project(request: Request):
    data = await request.json()
    al = AlarmListener()
    if data['hidden']:
        await al.stop_project_listener(
            data['project_id'], data['project_name'], message='Project stop due to move to hidden'
        )
    else:
        await al.start_project_listener(
            data['project_id'], data['project_name']
        )

    await LifecycleQuery.set_hide_in_project(project_id=data['project_id'], hidden=data['hidden'])


@router.delete('/delete_project')
async def delete_project(request: Request):
    data = await request.json()
    await LifecycleQuery.delete_project(data['project_id'])


@router.post('/get_real_projects_heartbeat')
async def get_real_projects_heartbeat():
    projects = await LifecycleQuery.get_real_projects_heartbeat()
    return projects



@router.get('/exceptions/{project_id}', response_class=HTMLResponse)
async def exception_pagination(request: Request, project_id: int, page: int = 1, page_size: int = 20):
    pr_name, exceptions, total_exceptions = await LifecycleQuery.get_exceptions_info_from_project(project_id, page, page_size)

    settings = await SettingsQuery.get_lf_settings()

    total_pages = (total_exceptions + page_size - 1) // page_size
    return templates.TemplateResponse(
        'exceptions.html', {
            'request': request,
            'exceptions': exceptions,
            'project_id': project_id,
            'page': page,
            'project_name': pr_name,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1,
            'next_page': page + 1,
            'previous_page': page - 1,
            'settings': settings,
        })


@router.get('/exceptions/{project_id}/delete/{exception_id}')
async def delete_exception(project_id: int, exception_id: int, page: int = 1, page_size: int = 20):
    await LifecycleQuery.delete_exception(exception_id)
    return RedirectResponse(url=f'/exceptions/{project_id}?page={page}&page_size={page_size}')

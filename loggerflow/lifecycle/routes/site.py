from loggerflow.lifecycle.database.queries import LifecycleQuery
from loggerflow.lifecycle.database import Database

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request, APIRouter

from pkg_resources import resource_filename

site_router = APIRouter()
db = Database()
templates_files_path = resource_filename('loggerflow.lifecycle', 'templates')
templates = Jinja2Templates(directory=templates_files_path)


@site_router.get('/', response_class=HTMLResponse)
async def start_loggerflow(request: Request):
    projects, total = await LifecycleQuery.get_all_projects()

    return templates.TemplateResponse('loggerflow.html', {'request': request, 'projects': projects, 'total': total})


@site_router.get('/hidden', response_class=HTMLResponse)
async def hidden(request: Request):
    projects, total = await LifecycleQuery.get_all_projects(hidden=True)
    return templates.TemplateResponse('hidden.html', {'request': request, 'projects': projects})


@site_router.post('/hide_or_return_project')
async def hilde_project(request: Request):
    data = await request.json()
    await LifecycleQuery.set_hide_in_project(project_id=data['project_id'], hidden=data['hidden'])


@site_router.delete('/delete_project')
async def delete_project(request: Request):
    data = await request.json()
    await LifecycleQuery.delete_project(data['project_id'])


@site_router.post('/get_real_projects_heartbeat')
async def get_real_projects_heartbeat():
    projects = await LifecycleQuery.get_real_projects_heartbeat()
    return projects


@site_router.get('/exceptions/{project_id}', response_class=HTMLResponse)
async def exception_pagination(request: Request, project_id: int, page: int = 1, page_size: int = 20):
    pr_name, exceptions, total_exceptions = await LifecycleQuery.get_exceptions_info_from_project(project_id, page, page_size)
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
            'previous_page': page - 1
        })


@site_router.get('/exceptions/{project_id}/delete/{exception_id}')
async def delete_exception(project_id: int, exception_id: int, page: int = 1, page_size: int = 20):
    await LifecycleQuery.delete_exception(exception_id)
    return RedirectResponse(url=f'/exceptions/{project_id}?page={page}&page_size={page_size}')

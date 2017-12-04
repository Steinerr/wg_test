import peewee_async
from aiohttp import web

from app.handlers import ProjectView, ClickView, EventView, RateView, ProjectRateView, StatisticsView
from app.models import db

app = web.Application()
app.db = db
app.objects = peewee_async.Manager(db)

app.router.add_route('*', '/project/', ProjectView)
app.router.add_route('*', '/project/{id}', ProjectView)

app.router.add_route('*', '/click/', ClickView)
app.router.add_route('*', '/click/{id}', ClickView)

app.router.add_route('*', '/event/', EventView)
app.router.add_route('*', '/event/{id}', EventView)

app.router.add_route('*', '/rate/', RateView)
app.router.add_route('*', '/rate/{id}', RateView)

app.router.add_route('*', '/projectrate/', ProjectRateView)
app.router.add_route('*', '/projectrate/{id}', ProjectRateView)

app.router.add_route('*', '/statistics/', StatisticsView)
app.router.add_route('*', '/statistics/{id}', StatisticsView)

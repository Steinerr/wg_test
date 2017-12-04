import peewee_async
from aiohttp import web
from playhouse.db_url import parse

from app import settings
from writer.handlers import WriterView

db_param = parse(settings.DATABASE_URL)
db = peewee_async.PostgresqlDatabase(**db_param)

app = web.Application()
app.db = db
app.objects = peewee_async.Manager(db)

app.router.add_route('*', '/', WriterView)

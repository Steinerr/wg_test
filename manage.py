from aiohttp import web
from manager import Manager

from app.app import app
from writer.app import app as writer_app

manager = Manager()


@manager.command
def runserver():
    web.run_app(app, host='0.0.0.0', port=8080)


@manager.command
def runwriter():
    web.run_app(writer_app, host='0.0.0.0', port=8070)


@manager.command
def init_db():
    import peewee
    from app.app import db
    from app.models import (
        Project,
        Click,
        Event,
        Rate,
        ProjectRate,
        Statistics,
    )

    db.set_allow_sync(True)

    print('Creating tables')
    for model in (Project, Click, Event, Rate, ProjectRate, Statistics):
        try:
            model.create_table()
        except peewee.ProgrammingError:
            db.close()
        else:
            print('Create %s' % model.__name__.lower())


if __name__ == '__main__':
    manager.main()

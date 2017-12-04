import peewee
from playhouse.db_url import parse
from peewee_async import PostgresqlDatabase
from app import settings
from app.cache import Cache

db_param = parse(settings.DATABASE_URL)
db = PostgresqlDatabase(**db_param)


PAYD_CONDITIONS = {
    'partner1': {
        'DE': {
            'wowp': {'tutorial',},
        },
        'FR': {
            'wowp': {'tutorial',},
        },
        'IT': {
            'wowp': {'tutorial',},
        },
    },
    'partner2': {
        'RU': {
            'wot': {'reg', 'tutorial',},
            'wows': {'reg', 'tutorial',},
        },
        'FR': {
            'wot': {'reg', 'tutorial',},
            'wows': {'reg', 'tutorial',},
        },
        'IT': {
            'wot': {'reg', 'tutorial',},
            'wows': {'reg', 'tutorial',},
        },
    }
}


class CustomBaseModel(peewee.Model):
    class Meta:
        database = db


class Project(CustomBaseModel):
    name = peewee.TextField()


class Click(CustomBaseModel):
    country = peewee.TextField()
    ad = peewee.TextField()
    partner = peewee.TextField()
    user_id = peewee.IntegerField()
    timestamp = peewee.DateTimeField()


class Event(CustomBaseModel):
    project = peewee.TextField()
    user_id = peewee.IntegerField()
    event = peewee.TextField()
    timestamp = peewee.DateTimeField()

    async def is_payd(self, app):
        # sql = """
        # SELECT * FROM event
        # INNER JOIN click ON (click.user_id = event.user_id)
        # WHERE event.user_id = {};
        # """.format(self.user_id)

        qs = (
            Event.select(Event, Click)
            .join(Click, peewee.JOIN.INNER, on=(Click.user_id == Event.user_id).alias('click'))
        )
        try:
            obj = await app.objects.get(qs, id=self.id)
        except (Event.DoesNotExist, Click.DoesNotExist):
            return None, {}

        try:
            payd = obj.event in Cache.get('PAYD_CONDITIONS', {})[obj.click.partner][obj.click.country][obj.project]
        except KeyError:
            payd = False
        return (
            payd,
            {
                'event': obj.event,
                'user_id': obj.user_id,
                'date': obj.timestamp.date(),
                'ad': obj.click.ad,
                'country': obj.click.country,
                'partner': obj.click.partner,
                'project': obj.project,
            }
        )

    @property
    def is_reg_event(self):
        return self.event == 'reg'

    @property
    def is_tutorial_event(self):
        return self.event == 'tutorial'


class Rate(CustomBaseModel):
    country = peewee.TextField()
    event = peewee.TextField()
    partner = peewee.TextField()
    value = peewee.IntegerField()

    @classmethod
    async def create_payd_conditions(cls, app):
        conditions = await app.objects.execute(
            Rate.select(Rate, ProjectRate, Project)
            .join(ProjectRate)
            .join(Project)
        )
        payd_conditions = {}
        for cond in conditions:
            if not payd_conditions.get(cond.partner):
                payd_conditions[cond.partner] = {}
            if not payd_conditions[cond.partner].get(cond.country):
                payd_conditions[cond.partner][cond.country] = {}
            if not payd_conditions[cond.partner][cond.country].get(cond.projectrate.project.name):
                payd_conditions[cond.partner][cond.country][cond.projectrate.project.name] = set()
            payd_conditions[cond.partner][cond.country][cond.projectrate.project.name].add(cond.event)
        Cache.set('PAYD_CONDITIONS', payd_conditions)
        return payd_conditions


class ProjectRate(CustomBaseModel):
    rate = peewee.ForeignKeyField(Rate)
    project = peewee.ForeignKeyField(Project)


class Statistics(CustomBaseModel):
    date = peewee.DateField()
    partner = peewee.TextField()
    ad = peewee.TextField()
    country = peewee.TextField()
    clicks = peewee.IntegerField(null=True)
    paid_events = peewee.IntegerField(null=True)
    unpaid_events = peewee.IntegerField(null=True)
    reg = peewee.IntegerField(null=True)
    tutorial = peewee.IntegerField(null=True)
    postbacks = peewee.IntegerField(null=True)
    expenses = peewee.IntegerField(null=True)

import json

import aiohttp
import async_timeout
from aiohttp import web

from app.cache import Cache
from app.models import Project, Rate, Event, Click, Statistics, ProjectRate


class CRUDHandler(web.View):

    model = None

    async def get(self):
        obj_id = self.request.match_info.get('id')
        if obj_id:
            obj = await self.get_object()
            if not obj:
                return self.http_404_response()
            data = self.serialize(obj)
        else:
            projects = await self.request.app.objects.execute(self.model.select())
            data = [self.serialize(p) for p in projects]
        return web.Response(
            content_type='application/json',
            body=json.dumps(data).encode(),
        )

    async def post(self):
        print('REQ:', self.model)
        data = await self.request.json()
        obj = await self.request.app.objects.create(self.model, **data)
        return web.Response(
            content_type='application/json',
            body=json.dumps(self.serialize(obj)).encode(),
        )

    async def put(self):
        obj = await self.get_object()
        if not obj:
            return self.http_404_response()
        data = await self.request.json()
        for k, v in data.items():
            setattr(obj, k, v)
        await self.request.app.objects.update(obj)
        return web.Response(
            content_type='application/json',
            body=json.dumps(self.serialize(obj)).encode(),
        )

    async def delete(self):
        obj = await self.get_object()
        if not obj:
            return self.http_404_response()
        await self.request.app.objects.delete(obj)
        return web.Response(
            content_type='application/json',
            body=json.dumps({'deleted': obj.id}).encode(),
        )

    def serialize(self, obj):
        raise NotImplemented

    async def get_object(self):
        try:
            return await self.request.app.objects.get(self.model, id=self.request.match_info.get('id'))
        except self.model.DoesNotExist:
            return None

    def http_404_response(self):
        return web.Response(status=404, text='%s does not exist' % self.model.__name__)


class ClickView(CRUDHandler):
    model = Click

    async def put(self):
        return web.Response(status=405)

    async def delete(self):
        return web.Response(status=405)

    def serialize(self, obj):
        return {
            'id': obj.id,
            'country': obj.country,
            'ad': obj.ad,
            'partner': obj.partner,
            'user_id': obj.user_id,
            'timestamp': str(obj.timestamp),
        }


class EventView(CRUDHandler):
    model = Event

    async def post(self):
        data = await self.request.json()
        event = await self.request.app.objects.create(self.model, **data)
        if not Cache.get('PAYD_CONDITIONS'):
            await Rate.create_payd_conditions(self.request.app)
        is_payd, full_info = await event.is_payd(self.request.app)

        if is_payd is not None:
            statistics_data = {
                'date': str(full_info['date']),
                'partner': full_info['partner'],
                'ad': full_info['ad'],
                'country': full_info['country'],
                'is_payd': is_payd,
                'reg': event.is_reg_event,
                'tutorial': event.is_tutorial_event,
                'project': event.project,
            }
            # if is_payd:
            #     sended = await self.send_to_partner(full_info)
            #     statistics_data['postbacks'] = int(sended)

            await self.send_to_statistics(statistics_data)

        return web.Response(
            content_type='application/json',
            body=json.dumps(self.serialize(event)).encode(),
        )

    async def put(self):
        return web.Response(status=405)

    async def delete(self):
        return web.Response(status=405)

    def serialize(self, obj):
        return {
            'id': obj.id,
            'project': obj.project,
            'user_id': obj.user_id,
            'event': obj.event,
            'timestamp': str(obj.timestamp),
        }

    # async def send_to_partner(self, full_info):
    #     payload = {
    #         'host': '%s.com' % full_info['partner'],
    #         **full_info,
    #     }
    #     url = 'http://{host}/{event}?user={user_id}&date={date}&ad={ad}&country={country}'.format(**payload)
    #     async with aiohttp.ClientSession() as session:
    #         with async_timeout.timeout(10):
    #             async with session.get(url) as response:
    #                 return response.status == 200

    async def send_to_statistics(self, statistics_data):
        url = 'http://localhost:8080/statistics/'
        async with aiohttp.ClientSession() as session:
            with async_timeout.timeout(10):
                resp = await session.post(
                    url,
                    data=json.dumps(statistics_data),
                    headers={'content-type': 'application/json'}
                )
                return resp.status == 200


class RateView(CRUDHandler):
    model = Rate

    def serialize(self, obj):
        return {
            'id': obj.id,
            'country': obj.country,
            'event': obj.event,
            'partner': obj.partner,
            'value': obj.value,
        }


class ProjectView(CRUDHandler):
    model = Project

    def serialize(self, obj):
        return {
            'id': obj.id,
            'name': obj.name,
        }


class ProjectRateView(CRUDHandler):
    model = ProjectRate

    def serialize(self, obj):
        return {
            'project': obj.project_id,
            'rate': obj.rate_id,
        }


class StatisticsView(CRUDHandler):
    model = Statistics

    async def post(self):
        data = await self.request.json()
        print('STAT:', data)
        stat_obj, created = await self.request.app.objects.get_or_create(
            self.model,
            date=data['date'],
            partner=data['partner'],
            ad=data['ad'],
            country=data['country'],
        )

        if created:
            stat_obj.paid_events = 0
            stat_obj.unpaid_events = 0
            stat_obj.reg = 0
            stat_obj.tutorial = 0
            stat_obj.clicks = 0

        stat_obj.paid_events += int(data.get('is_payd', 0))
        stat_obj.unpaid_events += int(not data.get('is_payd', 0))
        stat_obj.reg += int(data.get('reg', 0))
        stat_obj.tutorial += int(data.get('tutorial', 0))
        stat_obj.clicks += 1
        stat_obj.expenses = await self.calculate_expenses(
            stat_obj.paid_events,
            data['partner'],
            data['country'],
            data['project'],
        )
        await self.request.app.objects.update(stat_obj)
        stat_obj = await self.request.app.objects.get(Statistics, id=stat_obj.id)
        return web.Response(
            content_type='application/json',
            body=json.dumps(self.serialize(stat_obj)).encode(),
        )

    async def calculate_expenses(self, payd_events, partner, country, project):
        try:
            rate = await self.request.app.objects.get(
                Rate.select(Rate)
                .join(ProjectRate)
                .join(Project).switch(Rate)
                .where(
                    Rate.country == country,
                    Rate.partner == partner,
                    Project.name == project,
                )
            )
        except Rate.DoesNotExist:
            return 0

        return rate.value * payd_events

    async def put(self):
        return web.Response(status=405)

    async def delete(self):
        return web.Response(status=405)

    def serialize(self, obj):
        return {
            'date': str(obj.date),
            'partner': obj.partner,
            'ad': obj.ad,
            'country': obj.country,
            'paid_events': obj.paid_events,
            'clicks': obj.clicks,
            'unpaid_events': obj.unpaid_events,
            'reg': obj.reg,
            'tutorial': obj.tutorial,
            'postbacks': obj.postbacks,
            'expenses': obj.expenses,
        }

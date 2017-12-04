import csv
import json

import aiohttp
import async_timeout
from aiohttp import web


class WriterView(web.View):
    async def get(self):
        print('======== load RATE ==========')
        await self._push_data('rate', 'rate.csv')

        print('======== load PROJECT ==========')
        await self._push_data('project', 'project.csv')

        print('======== load PROJECTRATE ==========')
        await self._push_data('projectrate', 'projectrate.csv')

        print('======== load CLICK ==========')
        await self._push_data('click', 'click.csv')

        print('======== load EVENT ==========')
        await self._push_data('event', 'event.csv')

        return web.Response(status=200)

    async def _push_data(self, url, csv_file):
        url = 'http://localhost:8080/%s/' % url
        with open('src/%s' % csv_file, newline='', encoding='utf-8') as csvfile:
            async with aiohttp.ClientSession() as session:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data = {k.strip(): v.strip() for k, v in row.items()}
                    print('%s DATA:' % csv_file.upper(), data)
                    with async_timeout.timeout(10):
                        resp = await session.post(
                            url,
                            data=json.dumps(data),
                            headers={'content-type': 'application/json'}
                        )

import os

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgres://wg_stat:qwerty@localhost:5432/wg_stat')

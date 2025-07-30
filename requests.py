import asyncpg
from aiogram import Bot
from app.token import TOKEN


class DBC:
    def __init__(self):
        self.pool = None
        self.bot = Bot(token=TOKEN)

    async def initialize_pool(self):
        self.pool = await asyncpg.create_pool(
            user='postgres',
            password='your_password',  # Write your postgres password
            database='name_of_db',  # Your db name
            host='localhost',
            port=5432,
            min_size=1,  # If this bot will use a lot of people increase max and min_size
            max_size=5
        )
        self.bot.pool = self.pool
        print('pool initialized')
        return self.pool

    async def record_id(self, tg_id):
        if not self.pool:
            raise RuntimeError('Pool not initialized')

        async with self.pool.acquire() as conn:
            try:
                await conn.execute('INSERT INTO notes(tg_id) VALUES($1)', tg_id)
            except asyncpg.exceptions.UniqueViolationError:
                print('This ID already in data base')

    async def binding_note(self, note, date, tg_id, num):
        if not self.pool:
            raise RuntimeError('Pool not initialized')
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('INSERT INTO notes_info(note, time, pers_id, num_id)'
                                   ' VALUES($1, $2, $3, $4)', note, date, tg_id, num)
        except asyncpg.exceptions.UniqueViolationError:
            print('This note already in data base')

    async def get_info(self, tg_id, num_id=None):
        if not self.pool:
            raise RuntimeError('Pool not initialized')
        async with self.pool.acquire() as conn:
            if num_id:
                inf = [record['note'] for record in
                       await conn.fetch('SELECT note FROM notes_info'
                                        ' WHERE pers_id = $1 AND num_id = $2', tg_id, num_id)]
                return inf
            inf = [record['note'] for record in
                   await conn.fetch('SELECT note FROM notes_info WHERE pers_id = $1', tg_id)]
            return inf

    async def remove_rec(self, note):
        if not self.pool:
            raise RuntimeError('Pool not initialized')
        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM notes_info WHERE note = $1', note)

    async def change_num_id(self, tg_id, arr: list):
        if not self.pool:
            raise RuntimeError('Pool not initialized')
        async with self.pool.acquire() as conn:
            for n, note in enumerate(arr):
                await conn.execute('UPDATE notes_info SET num_id = $1 WHERE note = $2 AND pers_id = $3',
                                   n+1, note, tg_id)

    async def get_full_info(self, tg_id):
        if not self.pool:
            raise RuntimeError('Pool not initialized')
        async with self.pool.acquire() as conn:
            inf = [[record['num_id'], record['note'], record['time']] for record
                   in await conn.fetch('SELECT num_id, note, time FROM notes_info WHERE pers_id = $1', tg_id)]
            return sorted(inf, key=lambda l: l[0])

    async def change(self, tg_id, num, new_note):
        if not self.pool:
            raise RuntimeError('Pool not initialized')
        async with self.pool.acquire() as conn:
            try:
                await conn.execute('UPDATE notes_info SET note = $1 WHERE pers_id = $2 AND num_id = $3',
                                   new_note, tg_id, num)
            except asyncpg.exceptions.PostgresError as e:
                print(f'{e}')

    async def on_shutdown(self):
        if hasattr(self.bot, 'pool') and self.bot.pool:
            await self.bot.pool.closed()

import asyncio
import aiohttp
import datetime
from more_itertools import chunked
from models import engine, Session, Base, SwapiPeople
import requests

CHUNK_SIZE = 10
responce = requests.get("https://swapi.dev/api/people")


async def get_people(session, people_id):
    async with session.get(f'https://swapi.dev/api/people/{people_id}') as response:
        json_data = await response.json()
        return json_data


async def paste_to_db(results):
    swapi_people = [SwapiPeople(birth_year=item.get('birth_year'),
                                eye_color=item.get('eye_color'),
                                films=str(item.get('films')).replace('[', '').replace(']', '').replace("'", ''),
                                gender=item.get('gender'),
                                hair_color=item.get('hair_color'),
                                height=item.get('height'),
                                homeworld=item.get('homeworld'),
                                mass=item.get('mass'),
                                name=item.get('name'),
                                skin_color=item.get('skin_color'),
                                species=str(item.get('species')).replace('[', '').replace(']', '').replace("'", ' '),
                                starships=str(item.get('starships')).replace('[', '').replace(']', '').replace("'", ' '),
                                vehicles=str(item.get('vehicles')).replace('[', '').replace(']', '').replace("'", ' '))
                    for item in results]

    async with Session() as session:
        session.add_all(swapi_people)
        await session.commit()


async def main():
    start = datetime.datetime.now()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session = aiohttp.ClientSession()

    coros = (get_people(session, i) for i in range(1, responce.json().get('count')+1))
    for coros_chunk in chunked(coros, CHUNK_SIZE):
        results = await asyncio.gather(*coros_chunk)

        asyncio.create_task(paste_to_db(results))

    await session.close()

    set_tasks = asyncio.all_tasks()
    for task in set_tasks:
        if task != asyncio.current_task():
            await task

    print(datetime.datetime.now() - start)

if __name__ == '__main__':
    asyncio.run(main())

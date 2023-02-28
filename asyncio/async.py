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
        if json_data.get('name'):
            coros_films = [get_films(session, i) for i in json_data.get('films')]
            results_films = await asyncio.gather(*coros_films)
            coros_species = [get_species(session, i) for i in json_data.get('species')]
            results_species = await asyncio.gather(*coros_species)
            coros_starships = [get_starships(session, i) for i in json_data.get('starships')]
            results_starships = await asyncio.gather(*coros_starships)
            coros_vehicles = [get_vehicles(session, i) for i in json_data.get('vehicles')]
            results_vehicles = await asyncio.gather(*coros_vehicles)
            coros_homeworld = [get_homeworld(session, json_data.get('homeworld'))]
            results_homeworld = await asyncio.gather(*coros_homeworld)

            json_data['films'] = ', '.join([i.get('title') for i in results_films])
            json_data['species'] = ', '.join([i.get('name') for i in results_species])
            json_data['starships'] = ', '.join([i.get('name') for i in results_starships])
            json_data['vehicles'] = ', '.join([i.get('name') for i in results_vehicles])
            json_data['homeworld'] = ', '.join([i.get('name') for i in results_homeworld])

        return json_data


async def get_films(session, films_url):
    async with session.get(films_url) as response:
        json_data = await response.json()
        return json_data


async def get_species(session, species_url):
    async with session.get(species_url) as response:
        json_data = await response.json()
        return json_data


async def get_starships(session, starships_url):
    async with session.get(starships_url) as response:
        json_data = await response.json()
        return json_data


async def get_vehicles(session, vehicles_url):
    async with session.get(vehicles_url) as response:
        json_data = await response.json()
        return json_data


async def get_homeworld(session, homeworld_url):
    async with session.get(homeworld_url) as response:
        json_data = await response.json()
        return json_data


async def paste_to_db(results):
    swapi_people = [SwapiPeople(birth_year=item.get('birth_year'),
                                eye_color=item.get('eye_color'),
                                films=item.get('films'),
                                gender=item.get('gender'),
                                hair_color=item.get('hair_color'),
                                height=item.get('height'),
                                homeworld=item.get('homeworld'),
                                mass=item.get('mass'),
                                name=item.get('name'),
                                skin_color=item.get('skin_color'),
                                species=item.get('species'),
                                starships=item.get('starships'),
                                vehicles=item.get('vehicles'))
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









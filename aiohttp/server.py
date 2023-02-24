import json
import uuid
from app import get_app
from aiohttp import web
from bcrypt import hashpw, gensalt
from db import engine, Base, Session, User, Token, Service
from sqlalchemy.exc import IntegrityError
from schema import validate_service, validate_user, Userval, Serviceval

app = get_app()


async def orm_context(app: web.Application):
    print('START')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # Миграции
    yield
    print('SHUTDOWN')
    await engine.dispose()


@web.middleware
async def session_middleware(requests: web.Request, handler):
    async with Session() as session:
        requests['session'] = session
        return await handler(requests)


app.cleanup_ctx.append(orm_context)  # Добавляем в приложение orm_context
app.middlewares.append(session_middleware)  # Подключаем middleware к приложению


def hash_password(password: str):
    password = password.encode()  # Преобразовываем пароль в байты
    password = hashpw(password, salt=gensalt())  # Хэшируем пароль
    return password.decode()  # Преобразовываем байты в строчку


async def get_user(user_id, session: Session):  # Извлекаем пользователя по его id
    user = await session.get(User, user_id)
    if user is None:
        raise web.HTTPNotFound(text=json.dumps({'status': 'error', 'message': 'user not found'}),
                               content_type='application/json')
    return user


async def get_service(service_id, session: Session):  # Извлекаем пользователя по его id
    service = await session.get(Service, service_id)
    if service is None:
        raise web.HTTPNotFound(text=json.dumps({'status': 'error', 'message': 'service not found'}),
                               content_type='application/json')
    return service


async def get_token(tok, session: Session):  # Извлекаем пользователя по его id
    token = await session.get(Token, tok)
    if token is None:
        raise web.HTTPNotFound(text=json.dumps({'status': 'error', 'message': 'token not found'}),
                               content_type='application/json')
    return token


class UserView(web.View):

    async def get(self):
        session = self.request['session']
        user_id = int(self.request.match_info['user_id'])  # Извлекаем id пользователя из объекта request
        user = await get_user(user_id, session)
        return web.json_response({
            'id': user.id,
            'name': user.name,
            'creation_time': user.creation_time.isoformat()
        })

    async def post(self):
        session = self.request['session']
        try:
            json_data = await self.request.json()
        except:
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'incorrect data'}),
                                   content_type='application/json')
        json_validate = validate_user(Userval, json_data)
        json_validate['password'] = hash_password(
            json_validate['password'])  # Извлекаем из json_data пароль Ложим обратно в словарь json_data
        user = User(**json_validate)  # Создаем объект пользователя
        session.add(user)  # Добавляем объект пользователя в сессию
        token = Token(user=user)
        session.add(token)
        try:
            await session.commit()  # Создаем коммит
        except IntegrityError as er:
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'user alredy exists'}),
                                   content_type='application/json')
        return web.json_response(
            {'id': user.id,
             'name': user.name,
             'token': str(token.id)}
        )

    async def patch(self):
        session = self.request['session']
        user_id = int(self.request.match_info['user_id'])  # Извлекаем id пользователя из объекта request
        user = await get_user(user_id, self.request['session'])  # Извлекаем пользователя по его id
        try:
            json_data = await self.request.json()  # Вытаскиваем данные из json которые вы передаем в методе по http
        except:
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'incorrect data'}),
                                   content_type='application/json')
        json_validate = validate_user(Userval, json_data)
        try:
            tok = uuid.UUID(self.request.headers.get('token'))
            # print(tok)
        except (ValueError, TypeError):
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'incorrect token'}),
                                   content_type='application/json')
        token = await get_token(tok, session)
        if user_id != token.user_id:
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'incorrect token'}),
                                   content_type='application/json')
        if 'password' in json_validate:
            json_validate['password'] = hash_password(json_validate['password'])
        for field, value in json_validate.items():  # Извлекаем поля и значения из json_data
            setattr(user, field, value)  # Устанавливаем правильные атрибуты у пользователя
        self.request['session'].add(user)  # Добавлем пользователя в сессию, которая находится в объекте request
        await self.request['session'].commit()
        return web.json_response({'status': 'success'})

    async def delete(self):
        session = self.request['session']
        user_id = int(self.request.match_info['user_id'])  # Извлекаем id пользователя из объекта request
        user = await get_user(user_id, self.request['session'])  # Извлекаем пользователя по его id
        try:
            tok = uuid.UUID(self.request.headers.get('token'))
        except (ValueError, TypeError):
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'incorrect token'}),
                                   content_type='application/json')
        token = await get_token(tok, session)
        if user_id != token.user_id:
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'incorrect token'}),
                                   content_type='application/json')
        await self.request['session'].delete(user)
        await self.request['session'].commit()
        return web.json_response({'status': 'success'})


class ServiceView(web.View):
    async def get(self):
        session = self.request['session']
        service_id = int(self.request.match_info['service_id'])  # Извлекаем id из объекта request
        service = await get_service(service_id, session)
        return web.json_response({
            'id': service.id,
            'heading': service.heading,
            'description': service.description
        })

    async def post(self):
        session = self.request['session']
        try:
            json_data = await self.request.json()
        except:
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'incorrect data'}),
                                   content_type='application/json')
        json_validate = validate_service(Serviceval, json_data)
        try:
            tok = uuid.UUID(self.request.headers.get('token'))
        except (ValueError, TypeError):
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'incorrect token'}),
                                   content_type='application/json')
        token = await get_token(tok, session)
        service = Service(**json_validate, user_id=token.user_id)  # Создаем объект пользователя
        session.add(service)  # Добавляем объект пользователя в сессию
        try:
            await session.commit()  # Создаем коммит
        except IntegrityError as er:
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'service alredy exists'}),
                                   content_type='application/json')
        return web.json_response(
            {'id': service.id,
             'heading': service.heading,
             'description': service.description
             }
        )

    async def patch(self):
        session = self.request['session']
        service_id = int(self.request.match_info['service_id'])  # Извлекаем id пользователя из объекта request
        service = await get_service(service_id, self.request['session'])  # Извлекаем пользователя по его id
        try:
            json_data = await self.request.json()  # Вытаскиваем данные из json которые вы передаем в методе по http
        except:
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'incorrect data'}),
                                   content_type='application/json')
        try:
            tok = uuid.UUID(self.request.headers.get('token'))
        except (ValueError, TypeError):
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'incorrect token'}),
                                   content_type='application/json')
        token = await get_token(tok, session)
        if service.user_id != token.user_id:
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'incorrect token'}),
                                   content_type='application/json')
        for field, value in json_data.items():  # Извлекаем поля и значения из json_data
            setattr(service, field, value)  # Устанавливаем правильные атрибуты у пользователя
        self.request['session'].add(service)  # Добавлем пользователя в сессию, которая находится в объекте request
        await self.request['session'].commit()
        return web.json_response({'status': 'success'})

    async def delete(self):
        session = self.request['session']
        service_id = int(self.request.match_info['service_id'])  # Извлекаем id пользователя из объекта request
        service = await get_service(service_id, self.request['session'])  # Извлекаем пользователя по его id
        try:
            tok = uuid.UUID(self.request.headers.get('token'))
            print(tok)
        except (ValueError, TypeError):
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'incorrect token'}),
                                   content_type='application/json')

        token = await get_token(tok, session)
        if service.user_id != token.user_id:
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'incorrect token'}),
                                   content_type='application/json')
        await self.request['session'].delete(service)
        await self.request['session'].commit()
        return web.json_response({'status': 'success'})


app.add_routes([
    web.get('/users/{user_id:\d+}/', UserView),
    web.post('/users/', UserView),
    web.patch('/users/{user_id:\d+}/', UserView),
    web.delete('/users/{user_id:\d+}/', UserView),

    web.get('/service/{service_id:\d+}/', ServiceView),
    web.post('/service/', ServiceView),
    web.patch('/service/{service_id:\d+}/', ServiceView),
    web.delete('/service/{service_id:\d+}/', ServiceView),

])

if __name__ == '__main__':
    web.run_app(app)

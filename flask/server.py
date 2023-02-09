from flask import jsonify, request
from flask.views import MethodView
from db import Service, Session, User, Token
from errors import HttpError
from schema import validate_create_service, validate, Register, Login
from flask_bcrypt import Bcrypt
from app import get_app
from auth import check_auth, check_password, hash_password
from crud import create_item, delete_item, get_item

app = get_app()
bcrypt = Bcrypt(app)


def register():
    user_data = validate(Register, request.json)
    with Session() as session:
        user_data["password"] = hash_password(user_data["password"])
        user = create_item(session, User, **user_data)
        return jsonify({"id": user.id, "username": user.username})


def login():
    login_data = validate(Login, request.json)
    with Session() as session:
        user = session.query(User).filter(User.e_mail == login_data["e_mail"]).first()
        if user is None or not check_password(user.password, login_data["password"]):
            raise HttpError(401, "Invalid user or password")
        token = Token(user=user)
        session.add(token)
        session.commit()
        return jsonify({"token": token.id})


@app.errorhandler(HttpError)
def error_handler(error: HttpError):
    http_response = jsonify({'status': 'error', 'description': error.message})
    http_response.status_code = error.status_code
    return http_response


def get_user(user_id: int, session: Session):
    user = session.query(User).get(user_id)
    print(user.id)
    if user is None:
        raise HttpError(404, 'service not found')
    return user


class UserView(MethodView):

    def get(self, user_id: int):
        with Session() as session:
            user = get_user(user_id, session)
            return jsonify({
                'id': user.id,
                'username': user.username
            })

    def patch(self, user_id: int):
        json_data = request.json
        with Session() as session:
            token = check_auth(session)
            user = get_item(session, User, user_id)
            if token.user_id != user.id:
                raise HttpError(403, "user has no access")
            user = get_user(user_id, session)
            for field, value in json_data.items():
                setattr(user, field, value)
            session.add(user)
            session.commit()

            return jsonify(
                {
                    "id": user.id,
                    "e_mail": user.e_mail,
                    "password": user.password,
                    "registration_time": user.registration_time.isoformat(),
                }
            )

    def delete(self, user_id: int):
        with Session() as session:
            user = get_item(session, User, user_id)
            token = check_auth(session)
            if token.user_id != user.id:
                raise HttpError(403, "user has no access")

            delete_item(session, user)

            return {"deleted": True}


def get_service(service_id: int, session: Session):
    service = session.query(Service).get(service_id)
    if service is None:
        raise HttpError(404, 'service not found')
    return service


class ServiceView(MethodView):

    def get(self, service_id: int):
        with Session() as session:
            service = get_service(service_id, session)
            return jsonify({
                'id': service.id,
                'heading': service.heading
            })

    def post(self):
        json_data = validate_create_service(request.json)
        with Session() as session:
            token = check_auth(session)
            if token:
                new_advertisement = Service(**json_data, user_id=token.user_id)
                session.add(new_advertisement)
                session.commit()
            else:
                raise ValueError('badly formed hexadecimal UUID string')
            return jsonify(
                {
                    'id': new_advertisement.id,
                    'creation_time': new_advertisement.creation_time.isoformat(),
                    'heading': new_advertisement.heading,
                }
            )

    def patch(self, service_id: int):
        json_data = validate_create_service(request.json)
        with Session() as session:
            token = check_auth(session)
            if token:
                service = get_service(service_id, session)
                if service.user_id == token.user_id:
                    for field, value in json_data.items():
                        setattr(service, field, value)
                    session.add(service)
                    session.commit()
                else:
                    raise HttpError(403, "user has no access")
            else:
                raise ValueError('badly formed hexadecimal UUID string')
            return jsonify(
                {
                    'status': 'The ad has been replaced',

                }
            )

    def delete(self, service_id: int):
        with Session() as session:
            token = check_auth(session)
            if token:
                service = get_service(service_id, session)
                if service.user_id == token.user_id:
                    service = get_service(service_id, session)
                    session.delete(service)
                    session.commit()
                else:
                    raise HttpError(403, "user has no access")
            else:
                raise ValueError('badly formed hexadecimal UUID string')
            return jsonify({'status': 'success'})


app.add_url_rule("/register", view_func=register, methods=["POST"])
app.add_url_rule("/login", view_func=login, methods=["POST"])

app.add_url_rule(
    "/user/<int:user_id>",
    view_func=UserView.as_view("user"),
    methods=["GET", "PATCH", "DELETE"],
)

app.errorhandler(HttpError)(error_handler)

app.add_url_rule('/service/<int:service_id>', view_func=ServiceView.as_view('ad_service_get'),
                 methods=['GET', "PATCH", 'DELETE'])
app.add_url_rule('/service', view_func=ServiceView.as_view('ad_service_post'), methods=['POST'])


if __name__ == "__main__":
    app.run(debug=True)

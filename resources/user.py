from os import environ

from flask_restful import Resource, abort
from flask_restful.reqparse import RequestParser
from marshmallow import ValidationError

from config import app, limiter
from model.user_model import *
from utils.common import get_random_alphanumeric_string

api_capacity = int(environ["DEFAULT_CAPACITY"])

user_create_requirements = RequestParser(bundle_errors=True)
user_create_requirements.add_argument("name", type=str, required=True, help="Name has to be passed")
user_create_requirements.add_argument("surname", type=str, required=True, help="Surname has to be passed")
user_create_requirements.add_argument("money_amount", type=float, required=True, help="Money Amount has to be passed")
user_create_requirements.add_argument("birthdate", type=str, required=True, help="Birthdate has to be passed")
user_create_requirements.add_argument("type", type=str, required=True, choices=("admin", "manager", "seller"),
                                      help="Type has to be passed")

user_update_requirements = RequestParser(bundle_errors=True)
user_update_requirements.add_argument("name", type=str, required=False, help="Name has to be passed")
user_update_requirements.add_argument("surname", type=str, required=False, help="Surname has to be passed")
user_update_requirements.add_argument("money_amount", type=float, required=False, help="Money Amount has to be passed")
user_update_requirements.add_argument("birthdate", type=lambda x: datetime.strptime(x, '%Y-%m-%d'),
                                      required=False, help="Birthdate has to be passed")
user_update_requirements.add_argument("type", type=str, required=False, choices=("admin", "manager", "seller"),
                                      help="Type has to be passed")

user_patch_requirements = RequestParser()
user_patch_requirements.add_argument("account_state", type=str, required=True,
                                     choices=("approved", "inProgress", "rejected"),
                                     help="Account State has to be passed")

users_list_schema = UserSchema(many=True)
user_schema = UserSchema()


def wrap_status_response(result):
    current_capacity = count_inProgress_user()
    response = {
        "capacity": f"{current_capacity} from {api_capacity}",
        "result": result
    }

    return response


def get_user_by_id(user_id):
    user = search_user_by_id(user_id)
    if not user:
        abort(404, message=f"Could not find user with id = {user_id}")
    return user


class Users(Resource):
    def get(self):
        users = UserModel.query. \
            order_by(UserModel.name). \
            filter(UserModel.account_state != "rejected"). \
            all()
        result = users_list_schema.dump(users)
        return wrap_status_response(result)

    def post(self):
        args = user_create_requirements.parse_args()
        current_capacity = count_inProgress_user()
        print(current_capacity)
        print(api_capacity)
        if current_capacity >= api_capacity:
            abort(429, message="Capacity Exceeded")
        try:
            data = user_schema.load(args)
        except ValidationError as err:
            return err.messages, 422
        username, password = get_random_alphanumeric_string(6), get_random_alphanumeric_string(6)
        new_user = UserModel(name=data['name'], surname=data['surname'],
                             type=data['type'], birthdate=data['birthdate'], money_amount=data['money_amount'],
                             username=username, password=password)

        db.session.add(new_user)
        db.session.flush()
        db.session.commit()
        return {"user_id": new_user.id, "username": username, "password": password}, 201


class User(Resource):

    def get(self, user_id):
        user = get_user_by_id(user_id)
        result = user_schema.dump(user)
        return wrap_status_response(result)

    def put(self, user_id):
        args = user_update_requirements.parse_args()
        user = get_user_by_id(user_id)
        for key in args.keys():
            if args[key]:
                user.__setattr__(key, args[key])
        update(user)
        return {"message": f"User with Id = {user_id}, was successfully Updated"}, 200

    def delete(self, user_id):
        get_user_by_id(user_id)
        UserModel.query.filter(UserModel.id == user_id).delete(synchronize_session=False)
        db.session.commit()
        return "", 204


def update(user):
    UserModel.query.filter(UserModel.id == user.id, UserModel.account_state != "rejected") \
        .update(user_schema.dump(user))
    db.session.commit()


@app.route(environ["API_BASE_PATH"] + "/users/<int:user_id>/status", methods=["PATCH"])
@limiter.exempt
def status_update(user_id):
    args = user_patch_requirements.parse_args()
    user = search_user_by_id(user_id)
    if not user:
        return {"message": f"Could not find user with id = {user_id}"}, 404
    else:
        time_diff = datetime.utcnow() - user.timestamp
        time_min = (time_diff.seconds // 60) % 60

    if time_min > 5:
        UserModel.query.filter(UserModel.id == user_id).update({UserModel.account_state: "rejected"},
                                                               synchronize_session=False)
        db.session.commit()
        return {"message": f"Time was exceeded for user with id = {user_id}"}, 400

    UserModel.query.filter(UserModel.id == user_id).update({UserModel.account_state: args['account_state']},
                                                           synchronize_session=False)
    db.session.commit()
    return {"message": f"Update User Status By Id  {user_id}"}, 200

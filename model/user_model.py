from config import db, ma_serializable
from marshmallow import fields
from datetime import datetime


class UserModel(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(32), nullable=False)
    surname = db.Column(db.String(32), nullable=False)
    type = db.Column(db.String(32), nullable=False)
    username = db.Column(db.String(32), nullable=True)
    password = db.Column(db.String(32), nullable=True)
    account_state = db.Column(db.String(32), nullable=False, default="inProgress")
    birthdate = db.Column(db.DateTime, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())


class UserSchema(ma_serializable.SQLAlchemyAutoSchema):
    birthdate = fields.Date()
    username = fields.String(load_only=True)
    password = fields.String(load_only=True)

    class Meta:
        model = UserModel


def search_user_by_id(user_id):
    return UserModel().query.filter(UserModel.id == user_id, UserModel.account_state != "rejected").first()


def count_inProgress_user():
    users = UserModel.query.filter(UserModel.account_state == "inProgress").all()
    return len(users)

import sqlalchemy
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class Items(SqlAlchemyBase, SerializerMixin, UserMixin):
    __tablename__ = 'items'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    photo = sqlalchemy.Column(sqlalchemy.VARCHAR, default='/static/images/old.png')
    image = sqlalchemy.Column(sqlalchemy.VARCHAR, default='/static/images/old.png')
    year = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    count_photo = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)

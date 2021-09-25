from peewee import SqliteDatabase, CharField, TextField, Model, DoesNotExist
from typing import Any

db = SqliteDatabase('users.db')


class User(Model):
    id_name = CharField()
    text = TextField()

    class Meta:
        database = db

    @classmethod
    def append_data(cls, id_name: int, new_text: str) -> None:

        id_name_exist = True

        try:
            User.select().where(User.id_name == id_name).get()
        except DoesNotExist:
            id_name_exist = False

        if id_name_exist:
            user_data = User.get(User.id_name == id_name)
            user_data.text += new_text
            user_data.save()

        else:
            user_data = User(id_name=id_name, text=new_text)
            user_data.save()

    @classmethod
    def output_data(cls, id_name: int) -> Any:

        try:
            data = User.select().where(User.id_name == id_name).get()
            return data.text
        except DoesNotExist:
            return None


with db:
    User.create_table()

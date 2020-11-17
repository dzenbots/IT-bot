from peewee import SqliteDatabase, Model, CharField, ForeignKeyField

from settings import DB_FILE_PATH

db = SqliteDatabase(DB_FILE_PATH, pragmas={'foreign_keys': 1})


class BaseModel(Model):
    class Meta:
        database = db


class Group(BaseModel):
    group_name = CharField(unique=True)


class User(BaseModel):
    telegram_id = CharField(unique=True)
    first_name = CharField()
    last_name = CharField()
    status = CharField()


class Links(BaseModel):
    user = ForeignKeyField(User, backref='links')
    group = ForeignKeyField(Group, backref='links')


class Equipment(BaseModel):
    it_id = CharField(unique=True)
    pos_in_buh = CharField()
    invent_num = CharField()
    type = CharField()
    mark = CharField()
    model = CharField()
    serial_num = CharField()


class Movement(BaseModel):
    equipment = ForeignKeyField(Equipment, backref="movements")
    campus = CharField()
    room = CharField()


class Person(BaseModel):
    name = CharField()
    surname = CharField()
    patronymic = CharField()
    position = CharField()
    photo = CharField()
    phone = CharField()
    email = CharField()
    actual = CharField()


def initialize_db():
    db.connect()
    db.create_tables([
        User,
        Group,
        Links,
        Equipment,
        Movement,
        Person
    ], safe=True)
    admin_group, created = Group.get_or_create(group_name='Admins')
    users_group, created = Group.get_or_create(group_name='Users')
    root, created = User.get_or_create(telegram_id='190737618',
                                       first_name='Dzen',
                                       last_name='Bots',
                                       defaults={
                                           'status': ''
                                       })
    Links.get_or_create(user=root,
                        group=admin_group)
    Links.get_or_create(user=root,
                        group=users_group)

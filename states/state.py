from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    waiting_for_phone = State()
    referrer_id = State()
    


class AddChannel(StatesGroup):
    waiting_for_channel_name = State()


class AddCourse(StatesGroup):
    waiting_for_course_username = State()
    just_name = State()
    waiting_for_course_point = State()


class forpoint(StatesGroup):
    waiting_for_new_points = State()


class msgtoall(StatesGroup):
    sendtoall = State()


class msgtoindividual(StatesGroup):
    sendtoone = State()
    userid = State()


class Adminid(StatesGroup):
    admin_id = State()
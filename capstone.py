import asyncio
import logging
import sys
import random
from typing import Any, Dict,AnyStr
import redis
from aiogram.fsm.storage.redis import RedisStorage
from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import(
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)

# Token
TOKEN = ""

# user
class User(StatesGroup):
    fullName = State()
    phone = State()
    role = State()
    id = State()
class Form(StatesGroup):
    register = State()
    login = State()
    management = State()
    booking = State()
    matching = State()
    rating = State()
    setRating = State()

form_router = Router()

REDIS_CLOUD_HOST = ''
REDIS_CLOUD_PORT = 0 # Replace with your Redis Cloud port
REDIS_CLOUD_PASSWORD = ''

redis_conn = redis.StrictRedis(
    host=REDIS_CLOUD_HOST,
    port=REDIS_CLOUD_PORT,
    password=REDIS_CLOUD_PASSWORD,
    decode_responses=True,
)

def keyCount():
    key_types_count = {}
    userList = []
    cursor = '0'
    while cursor != 0:
        cursor, keys = redis_conn.scan(cursor=cursor)  # Adjust count based on your dataset size
        for key in keys:
            key_type = redis_conn.type(key)

            # Count the key type
            key_types_count[key_type] = key_types_count.get(key_type, 0) + 1
            if key_type == "hash":
                userList.append(key)

    # Break the loop if the cursor is '0', indicating the end of keys 
    return userList

@form_router.message(CommandStart())
async def process_start(message:Message, state:FSMContext):
    await message.reply(
        text = f"welcome to Rideshare Bot {html.quote(message.from_user.full_name)}!"
    )
    flag = False
    userList = keyCount()
    id = str(message.from_user.id)
    for user in userList:
        if user == id:
            flag = True
            break
    if not flag:
        await state.set_state(Form.register)
        await message.answer(
            text = "please register first",
            reply_markup=ReplyKeyboardMarkup(

                keyboard=[
                    [
                        KeyboardButton(text="Register")
                    ]

                ],
                resize_keyboard=True
            )
        )
    else:
        await state.set_state(Form.login)
        await login_service(message=message, state=state)

@form_router.message(Form.register, F.text.casefold() == "register")
@form_router.message(Command("/register"))
async def process_register_user(message:Message, state:FSMContext):
    await state.set_state(Form.register)
    await message.reply(
        text= "please enter the following credentials",

    )
    await profile_edit_choice(message=message)
    

@form_router.message(Form.register, F.text.casefold() == "fullname")
async def process_register_fullname(message:Message, state:FSMContext):
    await state.set_state(User.fullName)
    await message.reply(
        text = "Enter your fullname",
        reply_markup=ReplyKeyboardRemove()
    )


@form_router.message(User.fullName)
async def process_user_fullname(message:Message, state:FSMContext):
    await state.set_state(Form.register)
    id = str(message.from_user.id)
    print(id)
    redis_conn.hset(id,"Fullname",message.text)
    await message.answer(
        text = "Fullname has been successfully added"
    )
    await profile_edit_choice(message=message)

@form_router.message(Form.register, F.text.casefold() == "role")
async def process_register_Role(message:Message, state:FSMContext):
    await state.set_state(User.role)
    await message.reply(
        text = "Enter your Role",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text = "Driver"),
                    KeyboardButton(text= "Passenger")
                ]
                
            ],
            resize_keyboard=True
        )
    )

@form_router.message(User.role)
async def process_user_role(message:Message, state:FSMContext):
    await state.set_state(Form.register)
    id = str(message.from_user.id)
    redis_conn.hset(id,"Role",message.text)
    redis_conn.hset(id,"stat","Free")
    await message.answer(
        text = "Role has been successfully added"
    )
    await profile_edit_choice(message=message)


@form_router.message(Form.register, F.text.casefold() == "phone")
async def process_register_phone(message:Message, state:FSMContext):
    await state.set_state(User.phone)
    await message.reply(
        text = "Enter your Phone number",
        reply_markup=ReplyKeyboardRemove()
    )

@form_router.message(User.phone)
async def process_user_phone(message:Message, state:FSMContext):
    await state.set_state(Form.register)
    id = str(message.from_user.id)
    redis_conn.hset(id,"Phone",message.text)
    await message.answer(
        text = "Phone has been successfully added"
    )
    await profile_edit_choice(message=message)

@form_router.message(Form.register, F.text.casefold() == "done")
async def process_register_done(message:Message, state:FSMContext):
    await state.set_state(Form.login)
    await message.reply(
        text = "Done with your profile, congratulations",
    )
    await login_service(message=message, state=state)


@form_router.message(Form.login, F.text.casefold() == "editprofile")
async def process_edit_profile(message:Message, state:FSMContext):
    await state.set_state(Form.register)
    await message.reply(
        text="Edit your credentials",
        reply_markup=ReplyKeyboardRemove()
    )
    await profile_edit_choice(message=message)

@form_router.message(Form.login, F.text.casefold() == "book")
async def process_ride_book(message:Message, state:FSMContext):
    await state.set_state(Form.booking)
    await message.reply(
        text ="Please allow bot to get your location",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="ShareLocation")
                ]
            ],
            resize_keyboard=True
        )
    )

@form_router.message(Form.booking,F.text.casefold() =="sharelocation")
async def process_ride_location(message:Message,state:FSMContext):
    await message.reply(
        text= "enter destination",
        reply_markup=ReplyKeyboardRemove()

    )
    
@form_router.message(Form.booking)
async def process_ride_destination(message:Message, state:FSMContext):
    await state.set_state(Form.login)
    redis_conn.hset(message.from_user.id,"Stat", "Busy")
    location = message.location
    if location:
        lat = message.location.latitude
        lon = message.location.longitude
        reply = "latitude:  {}\nlongitude: {}".format(lat, lon)
    else:
        reply = "current postion"
    startTime = random.randint(1,24)
    endTime = random.randint(1,60)
    text = "from " + reply + " to " + message.text + "\nstart time: " + str(startTime) + ":00 to " + str(startTime)+":" + str(endTime)
    
    await message.reply(
        text= text,
        reply_markup=ReplyKeyboardRemove()
    )

    hist_hash = str(message.from_user.id) + "book"
    redis_conn.lpush(hist_hash,"1?" + text) 
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    userList = keyCount()
    id = str(message.from_user.id)
    for user in userList:
        if redis_conn.hget(user,"Role") == "Driver" and redis_conn.hget(user,"Stat") == "Free":
            redis_conn.hset(user,"Passenger", id)
            await bot.send_message(chat_id=int(user), text="Alert: nearby driver requested a ride " + text, reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text="Accept"),
                        KeyboardButton(text = "Cancel")
                    ]
                ],
                resize_keyboard=True
            ))

    await login_service(message=message, state=state)

@form_router.message(Form.matching, F.text.casefold() == "accept")
async def process_matching_accept(message:Message, state:FSMContext):
    passenger = redis_conn.hget(str(message.from_user.id), "Passenger")
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    await bot.send_message(chat_id=int(passenger), text = "Driver is enroute")
    redis_conn.hset(message.from_user.id,"Stat", "Busy")
    await message.reply(
        text="ride has been accepted",
        reply_markup=ReplyKeyboardRemove()
    )
    await login_service(message=message, state=state)

@form_router.message(Form.matching, F.text.casefold() == "cancel")
async def process_matching_cancel(message:Message, state:FSMContext):
    await message.reply(
        text="ride has been cancelled",
        reply_markup=ReplyKeyboardRemove()
    )
    await login_service(message=message, state=state)

@form_router.message(Form.matching, F.text.casefold() == "completed")
async def process_matching_cancel(message:Message, state:FSMContext):
    redis_conn.hset(message.from_user.id, "Stat", "Free")
    
    await message.reply(
        text="ride has been completed",
        reply_markup=ReplyKeyboardRemove()
    )
    await login_service(message=message, state=state)

@form_router.message(Form.login, F.text.casefold() == "rate")
async def process_ride_rating(message:Message, state:FSMContext):
    hist_hash = str(message.from_user.id) + "book"
    length = redis_conn.llen(hist_hash)
    history = redis_conn.lrange(hist_hash,0,length)
    for index,hist in enumerate(history):
        rate, text = map(str,hist.split("?"))
        await message.answer(
            text = "Ride: " + str(index+1) +"\nRate: " + rate +"\nText: " + text,
            reply_markup=ReplyKeyboardRemove()
        )
    await state.set_state(Form.rating)

    await message.reply(
        text="select index of ride to rate",
        reply_markup=ReplyKeyboardRemove()
    )

@form_router.message(Form.rating)
async def process_ride_index(message:Message, state:FSMContext):
    hist_hash = str(message.from_user.id) + "book"
    length = redis_conn.llen(hist_hash)
    history = redis_conn.lrange(hist_hash,0,length)
    if not message.text.isdigit() or int(message.text) < 0 or int(message.text) > length:
        await state.set_state(Form.login)
        process_ride_rating(message = message, state = state)
    else:
        index = int(message.text)
        await state.set_state(Form.setRating)
        await state.update_data(index = index)
        await message.reply(
            text="enter new rating from 0 to 5",
            reply_markup=ReplyKeyboardRemove()
        )
        
@form_router.message(Form.setRating)
async def process_add_rating(message:Message, state:FSMContext):
    await state.set_state(Form.login)
    dicts = await state.get_data()
    index = int(dicts["index"])
    hist_hash = str(message.from_user.id) + "book"
    length = redis_conn.llen(hist_hash)
    history = redis_conn.lrange(hist_hash,0,length)
    rating = message.text
    print(type(rating),rating.isdigit(),rating, index, int(rating) < 0, int(rating) > 5)
    if not rating.isdigit() or int(rating) < 0 or int(rating) > 5:
        rating = 1
    else:
        rating = int(rating)
    history[index-1] = str(rating) + history[index-1][1:]
    print(history[index-1])
    redis_conn.lset(hist_hash,index-1,history[index-1])

    await message.reply(
        text="Rating updated successfully",
        reply_markup=ReplyKeyboardRemove()
    )

    await login_service(message=message, state=state)

@form_router.message(Form.login, F.text.casefold() == "history")
async def process_ride_history(message:Message, state:FSMContext):
    hist_hash = str(message.from_user.id) + "book"
    length = redis_conn.llen(hist_hash)
    history = redis_conn.lrange(hist_hash,0,length)
    for hist in history:
        rate, text = map(str,hist.split("?"))
        await message.answer(
            text = "Rate: " + rate +"\nText: " + text,
            reply_markup=ReplyKeyboardRemove()
        )
    await state.set_state(Form.login)
    await login_service(message=message, state=state)

async def profile_edit_choice(message:Message):
    await message.answer(
        text="choose one",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Fullname"),
                    KeyboardButton(text="Phone"),
                    KeyboardButton(text="Role"),
                    KeyboardButton(text="Done")
                ]
            ],
            resize_keyboard=True
        )
    )

async def login_service(message:Message, state:FSMContext):
    id = str(message.from_user.id)
    if redis_conn.hget(id,"Role") == "Passenger":
        await message.answer(
                text ="select one of the follwing services",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [
                            KeyboardButton(text="EditProfile"),
                            KeyboardButton(text="Book"),
                            KeyboardButton(text="Rate"),
                            KeyboardButton(text="History")
                        ]
                    ],
                    resize_keyboard=True
                )
            )
    else:
        await state.set_state(Form.matching)
        if redis_conn.hget(message.from_user.id, "Stat") == "Free":
            await message.answer(
                text = "Accept Rides"
            )
        else:
            await message.answer(
                text = "click complete when you finish the ride",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [
                            KeyboardButton(text="Completed")
                        ]
                    ],
                    resize_keyboard=True
                )
            )

async def main():
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(form_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

import json
import aiogram
import re
from aiogram.utils import exceptions
from db_handler import dbHandler
from scheduleBot_Manager import ScheduleBotManager


class ScheduleBotManagerTGAPI:
    def __init__(self, curr_path, config_path, config_private_path):
        with open(
                curr_path + config_private_path,
                encoding='utf-8'
        ) as json_file:
            config_private = json.load(json_file)
        self.manager = ScheduleBotManager(curr_path, config_path)
        self.curr_path = curr_path
        self.bot_token = config_private.get("bot_token")
        self.db_url = config_private.get("db_url")
        self.bot = aiogram.Bot(self.bot_token)
        self.dp = aiogram.Dispatcher(self.bot)
        self.db = dbHandler(self.db_url)

    # Core Functions :

    async def get_info(self, message=aiogram.types.message.Message):
        group_bool = message.chat.type != 'private'

        username = message.from_user.username
        username = username if username else "None"

        print(message.from_user.id)
        try:
            print(message.from_user.first_name)
        except Exception:
            print("UNICODE")

        try:
            print(message.from_user.last_name)
        except Exception:
            print("UNICODE")

        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        if not first_name and not last_name:
            nameofuser = "OH FUCKING SHIET ERR"
        elif not message.from_user.first_name:
            nameofuser = last_name
        elif not message.from_user.last_name:
            nameofuser = first_name
        else:
            nameofuser = first_name + ' ' + last_name

        print(1)

        response_arr = self.db.get_info_msgNEW(
            message.from_user.id,
            username,
            nameofuser,
            group_bool,
            message.chat.id,
            message.chat.title
        )

        xls_response = self.manager.xls.find_timetable(response_arr[0], dict())
        if not response_arr[0] or xls_response == dict():
            group = "NULL"
        else:
            group = response_arr[0]
            if not self.manager.timetable.get(group):
                self.manager.timetable = self.manager.xls.find_timetable(
                    response_arr[0],
                    self.manager.timetable
                )

        admin_bool = True if response_arr[1] == 1 else False
        print(2)
        return [
            group,
            admin_bool,
            message.chat.title if group_bool is True else nameofuser
        ]

    def close(self):
        self.db.close()

    # Message Handling & Responsing Functions :

    async def start(self, message=aiogram.types.message.Message):
        response = await self.get_info(message)
        response_message = await self.manager.start_response(name=response[2])
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def rozklad(self, message=aiogram.types.message.Message):
        await self.get_info(message)
        new_group = message.text[8:].strip().lower()

        response = await self.manager.rozklad_response(new_group)
        if response[0] is True:
            self.db.upd_chat_rozklad(message.chat.id, new_group)
        response_message = response[1]

        await self.bot.send_message(message.chat.id, response_message)
        print(new_group)

    async def quick_help(self, message=aiogram.types.message.Message):
        await self.get_info(message)
        response_message = await self.manager.quick_help_response()
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    # RUSSISCH LANGUAGE
    async def help(self, message=aiogram.types.message.Message):
        response = await self.get_info(message)
        response_message = await self.manager.help_response(group=response[0])

        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def today(self, message=aiogram.types.message.Message):
        response = await self.get_info(message)
        group_response = await self.group_response(message, response, "today")

        if group_response[0] is False:
            response_message = group_response[1]

        else:
            group = group_response[1]
            name = response[2]
            response_message = await self.manager.today_response(group, name)

        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def tomorrow(self, message=aiogram.types.message.Message):
        response = await self.get_info(message)
        group_response = await self.group_response(
            message,
            response,
            "tomorrow"
        )

        if group_response[0] is False:
            response_message = group_response[1]

        else:
            group = group_response[1]
            name = response[2]
            response_message = await self.manager.tomorrow_response(
                group, name
            )

        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def week(self, message=aiogram.types.message.Message):
        response = await self.get_info(message)
        group_response = await self.group_response(message, response, "week")

        if group_response[0] is False:
            response_message = group_response[1]

        else:
            response_message = await self.manager.week_response(
                group=group_response[1]
            )

        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def next_week(self, message=aiogram.types.message.Message):
        response = await self.get_info(message)
        group_response = await self.group_response(
            message,
            response,
            "nextweek"
        )

        if group_response[0] is False:
            response_message = group_response[1]

        else:
            response_message = await self.manager.next_week_response(
                group=group_response[1]
            )

        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def full(self, message=aiogram.types.message.Message):
        response = await self.get_info(message)
        group_response = await self.group_response(message, response, "full")

        if group_response[0] is False:
            response_message = group_response[1]

        else:
            response_message = await self.manager.full_response(
                group=group_response[1]
            )

        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def current_lesson(self, message=aiogram.types.message.Message):
        response = await self.get_info(message)
        group_response = await self.group_response(
            message,
            response,
            "currentlesson"
        )

        if group_response[0] is False:
            response_message = group_response[1]

        else:
            response_message = await self.manager.current_lesson_response(
                group=group_response[1],
                name=response[2]
            )

        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def next_lesson(self, message=aiogram.types.message.Message):
        response = await self.get_info(message)
        group_response = await self.group_response(
            message,
            response,
            "nextlesson"
        )

        if group_response[0] is False:
            response_message = group_response[1]

        else:
            response_message = await self.manager.next_lesson_response(
                group=group_response[1],
                name=response[2]
            )

        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )
        return

    async def timetable_mes(self, message=aiogram.types.message.Message):
        await self.get_info(message)
        response_message = await self.manager.timetable_mes_response()
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def left(self, message=aiogram.types.message.Message):
        response = await self.get_info(message)
        name = response[2]
        response_message = await self.manager.left_response(name)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    # ENGLISH LANGUAGE
    async def find_info(self, message=aiogram.types.message.Message):
        await self.get_info(message)
        info_request = message.text[message.entities[0].length:].strip()
        response_message = await self.manager.find_info_response(info_request)
        try:
            await self.bot.send_message(
                message.chat.id,
                response_message,
                parse_mode='Markdown'
            )
        except aiogram.utils.exceptions.MessageIsTooLong:
            response_message = f"Err in message.\n" \
                               f"It is too long."
            await self.bot.send_message(
                message.chat.id,
                response_message,
                parse_mode='Markdown'
            )

    async def change_week(self, message=aiogram.types.message.Message):
        response = await self.get_info(message)
        admin_bool = response[1]
        if admin_bool is True:
            response_message = "ADMIN MODE"
            await self.bot.send_message(message.chat.id, response_message)
            #
            # LOG THIS ACTION!
            #
            response_message = await self.manager.change_week()
            await self.bot.send_message(message.chat.id, response_message)
        else:
            response_message = "You are not admin, get out of here!"
            await self.bot.send_message(message.chat.id, response_message)

    async def update_file(self, message=aiogram.types.message.Message):
        response = await self.get_info(message)
        admin_bool = response[1]
        if admin_bool is True:
            response_message = "ADMIN MODE"
            await self.bot.send_message(message.chat.id, response_message)
            url = message.text[message.entities[0].length:].strip()
            response = await self.manager.update_file(url)
            #
            # LOG THIS ACTION!
            #
            response_message = response[1]
            if response[0] is True:
                await self.send_everyone(response_message, 'HTML')
            else:
                await self.bot.send_message(message.chat.id, response_message)
        else:
            response_message = "You are not admin, get out of here!"
            await self.bot.send_message(message.chat.id, response_message)

    # Additional Functions:

    async def get_group_from_message(self, message):
        group = re.sub('[-]', '', message)
        if self.manager.timetable.get(group):
            return [True, group]
        elif self.manager.xls.find_timetable(group, dict()) != dict():
            self.manager.timetable = self.manager.xls.find_timetable(
                group,
                self.manager.timetable
            )
            return [True, group]
        else:
            return [
                False,
                f"Група не була знайдена. Мабуть, її немає в таблиці, "
                f"чи була допущена помилка, під час її написання."
            ]

    async def group_response(
            self,
            message=aiogram.types.message.Message,
            response=None,
            command=None
    ):
        group = response[0]

        if len(message.text) > message.entities[0].length:
            group_arr = await self.get_group_from_message(
                message.text[message.entities[0].length:].strip()
            )
            if group_arr[0] is False:
                await self.bot.send_message(
                    message.chat.id,
                    group_arr[1],
                    parse_mode='Markdown'
                )
                return [False, group_arr[1]]
            group = group_arr[1]

        if group == "NULL":
            response_message = f"Ваша поточна група: ***NULL***\n" \
                               f"Спробуйте додати групу наприкінці запросу. " \
                               f"Наприклад: `/{command} фі-73` \n" \
                               f"Або задайте групу таким чином: " \
                               f"`/rozklad фі-73`"
            return [False, response_message]
        return [True, group]

    async def send_everyone(self, response_message, parse_mode):
        chat_ids = self.db.get_chatIds()
        deleted_chats = list()
        for elem in chat_ids:
            try:
                await self.bot.send_message(
                    elem[0],
                    response_message,
                    parse_mode=parse_mode
                )
            except aiogram.utils.exceptions.ChatNotFound:
                deleted_chats.append(elem[0])
        '''
        if len(deleted_chats) > 0:
            self.db.delete_chats(deleted_chats)
        '''

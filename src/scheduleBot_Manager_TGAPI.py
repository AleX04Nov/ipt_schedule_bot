import json
import logging
import re
from logging.handlers import RotatingFileHandler

import aiogram
from aiogram.utils import exceptions

from db_handler import dbHandler
from scheduleBot_Manager import ScheduleBotManager


class ScheduleBotTGAPI:
    bot_token: str
    curr_path: str
    db_url: str
    bot: aiogram.Bot
    dp: aiogram.Dispatcher
    db: dbHandler
    manager: ScheduleBotManager

    def __init__(self, curr_path, config_path, config_private_path):
        with open(
                curr_path + config_private_path,
                encoding='utf-8'
        ) as json_file:
            config_private = json.load(json_file)
        self.bot_token = config_private.get("bot_token")
        self.curr_path = curr_path
        self.db_url = config_private.get("db_url")
        self.bot = aiogram.Bot(self.bot_token)
        self.dp = aiogram.Dispatcher(self.bot)
        self.db = dbHandler(self.db_url, curr_path)
        self.manager = ScheduleBotManager(curr_path, config_path)

        self.logger = logging.getLogger('scheduleBot_TGAPI')
        self.console_logger = logging.getLogger('CONscheduleBot_TGAPI')
        self.console_logger.setLevel(logging.INFO)

        hdlr = RotatingFileHandler(
            f"{curr_path}..\\data\\scheduleBot_TGAPI.log",
            mode='a',
            maxBytes=12 * 1024 * 1024,
            backupCount=2,
        )
        ch = logging.StreamHandler()

        log_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%d.%m.%Y | %H:%M:%S'
        )
        hdlr.setFormatter(log_format)
        ch.setFormatter(log_format)
        ch.setLevel(logging.INFO)

        self.logger.addHandler(hdlr)
        self.console_logger.addHandler(ch)

        return

    # Core Functions :

    async def get_info(self, message: aiogram.types.message):
        group_bool = message.chat.type != 'private'

        username = message.from_user.username
        username = username if username else "None"

        first_name = message.from_user.first_name
        last_name = message.from_user.last_name

        entity = message.entities[0]
        command = message.text[entity.offset: entity.length]
        self.console_logger.info(f"{first_name} {last_name} | {command}")

        if not first_name:
            nameofuser = last_name
        elif not last_name:
            nameofuser = first_name
        else:
            nameofuser = first_name + ' ' + last_name

        group, admin = self.db.get_info_msgNEW(
            message.from_user.id,
            username,
            nameofuser,
            group_bool,
            message.chat.id,
            message.chat.title
        )

        xls_response = self.manager.xls.find_timetable(group, dict())
        if not group or xls_response == dict():
            group = "NULL"
        else:
            if not self.manager.timetable.get(group):
                self.manager.timetable = self.manager.xls.find_timetable(
                    group,
                    self.manager.timetable
                )

        admin_bool = True if admin == 1 else False

        return (
            group,
            admin_bool,
            message.chat.title if group_bool is True else nameofuser
        )

    def close(self):
        self.db.close()

    # Message Handling & Responding Functions :

    async def start(self, message: aiogram.types.message):
        response = await self.get_info(message)
        response_message = await self.manager.start_response(name=response[2])
        await self.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def rozklad(self, message: aiogram.types.message):
        await self.get_info(message)
        new_group = message.text[8:].strip().lower()

        success, response_message = await self.manager.rozklad_response(
            new_group
        )
        if success is True:
            self.db.upd_chat_rozklad(message.chat.id, new_group)

        await self.send_message(message.chat.id, response_message)

    async def quick_help(self, message: aiogram.types.message):
        await self.get_info(message)
        response_message = await self.manager.quick_help_response()
        await self.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def help(self, message: aiogram.types.message):
        response = await self.get_info(message)
        response_message = await self.manager.help_response(group=response[0])

        await self.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def today(self, message: aiogram.types.message):
        response = await self.get_info(message)
        success, group = await self.group_response(message, response, "today")

        if success is False:
            response_message = group

        else:
            name = response[2]
            response_message = await self.manager.today_response(group, name)

        await self.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def tomorrow(self, message: aiogram.types.message):
        response = await self.get_info(message)
        success, group = await self.group_response(
            message,
            response,
            "tomorrow"
        )

        if success is False:
            response_message = group

        else:
            name = response[2]
            response_message = await self.manager.tomorrow_response(
                group, name
            )

        await self.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def week(self, message: aiogram.types.message):
        response = await self.get_info(message)
        success, group = await self.group_response(message, response, "week")

        if success is False:
            response_message = group

        else:
            response_message = await self.manager.week_response(
                group=group
            )

        await self.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def next_week(self, message: aiogram.types.message):
        response = await self.get_info(message)
        success, group = await self.group_response(
            message,
            response,
            "nextweek"
        )

        if success is False:
            response_message = group

        else:
            response_message = await self.manager.next_week_response(
                group=group
            )

        await self.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def full(self, message: aiogram.types.message):
        response = await self.get_info(message)
        success, group = await self.group_response(message, response, "full")

        if success is False:
            response_message = group

        else:
            response_message = await self.manager.full_response(
                group=group
            )

        await self.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def current_lesson(self, message: aiogram.types.message):
        response = await self.get_info(message)
        success, group = await self.group_response(
            message,
            response,
            "currentlesson"
        )

        if success is False:
            response_message = group

        else:
            response_message = await self.manager.current_lesson_response(
                group=group,
                name=response[2]
            )

        await self.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def next_lesson(self, message: aiogram.types.message):
        response = await self.get_info(message)
        success, group = await self.group_response(
            message,
            response,
            "nextlesson"
        )

        if success is False:
            response_message = group

        else:
            response_message = await self.manager.next_lesson_response(
                group=group,
                name=response[2]
            )

        await self.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def timetable_mes(self, message: aiogram.types.message):
        await self.get_info(message)
        response_message = await self.manager.timetable_mes_response()
        await self.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def left(self, message: aiogram.types.message):
        response = await self.get_info(message)
        name = response[2]
        response_message = await self.manager.left_response(name)
        await self.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def find_info(self, message: aiogram.types.message):
        await self.get_info(message)
        info_request = message.text[message.entities[0].length:].strip()
        response_message = await self.manager.find_info_response(info_request)
        success, error = await self.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )
        if success is False and type(error) == exceptions.MessageIsTooLong:
            response_message = (
                f"Помилка у повідомленні.\n"
                f"Занадто велике."
            )
            await self.send_message(
                message.chat.id,
                response_message,
                parse_mode='Markdown'
            )

    async def change_week(self, message: aiogram.types.message):
        response = await self.get_info(message)
        admin_bool = response[1]
        if admin_bool is True:
            response_message = "ADMIN MODE"
            await self.send_message(message.chat.id, response_message)
            response_message = await self.manager.change_week()
            self.logger.warning(f"Admin has changed "
                                f"week_index to {self.manager.week_index}")
            await self.send_message(message.chat.id, response_message)
        else:
            response_message = "Ти не адмін, забирайся звідси!"
            await self.send_message(message.chat.id, response_message)

    async def update_file(self, message: aiogram.types.message):
        response = await self.get_info(message)
        admin_bool = response[1]
        if admin_bool is True:
            response_message = "ADMIN MODE"
            await self.send_message(message.chat.id, response_message)
            url = message.text[message.entities[0].length:].strip()
            response = await self.manager.update_file(url)
            self.logger.warning(f"Admin is updating xls file on {url}")
            response_message = response[1]
            if response[0] is True:
                self.logger.warning(f"XLS Updated successfully")
                await self.send_everyone(response_message, 'HTML')
            else:
                self.logger.error(f"XLS Updating error")
                await self.send_message(message.chat.id, response_message)
        else:
            response_message = "Ти не адмін, забирайся звідси!"
            await self.send_message(message.chat.id, response_message)

    # Additional Functions:

    async def get_group_from_message(self, message: str):
        group = re.sub('[-]', '', message)
        if self.manager.timetable.get(group):
            return True, group
        elif self.manager.xls.find_timetable(group, dict()) != dict():
            self.manager.timetable = self.manager.xls.find_timetable(
                group,
                self.manager.timetable
            )
            return True, group
        else:
            return (
                False,
                f"Група не була знайдена. Мабуть, її немає в таблиці, "
                f"чи була допущена помилка, під час її написання."
            )

    async def group_response(
            self,
            message: aiogram.types.message,
            response=None,
            command=None
    ):
        group = response[0]
        if len(message.text) > message.entities[0].length:
            success, group = await self.get_group_from_message(
                message.text[message.entities[0].length:].strip()
            )
            if success is False:
                response_message = group
                return False, response_message

        if group == "NULL":
            response_message = (
                f"Ваша поточна група: ***NULL***\n"
                f"Спробуйте додати групу наприкінці запросу. "
                f"Наприклад: `/{command} фі-73` \n"
                f"Або задайте групу таким чином: "
                f"`/rozklad фі-73`"
            )
            return False, response_message
        return True, group

    async def send_everyone(self, response_message, parse_mode):
        chat_ids = self.db.get_chatIds()
        deleted_chats = list()
        for elem in chat_ids:
            success, err_type = await self.send_message(
                elem[0],
                response_message,
                parse_mode=parse_mode
            )
            if success is False and type(err_type) == exceptions.ChatNotFound:
                deleted_chats.append(elem[0])
        '''
        if len(deleted_chats) > 0:
            self.db.delete_chats(deleted_chats)
        '''

    async def send_message(self, chat_id, text, parse_mode=None):
        success_bool = True
        try:
            my_message = await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode
                )
        except Exception as e:
            success_bool = False
            self.logger.error(f"send_message \t{e}")
            my_message = e
        return success_bool, my_message

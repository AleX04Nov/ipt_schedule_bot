import json
import aiogram
import re
import datetime
import requests
from xls_handler import XlsHandler
from xls_handler import get_key
from db_handler import dbHandler


class ScheduleBot_Manager:
    def __init__(self, config_path, config_private_path):
        with open(config_path, encoding = 'utf-8') as json_file:
            config = json.load(json_file)
        with open(config_private_path, encoding = 'utf-8') as json_file:
            config_private = json.load(json_file)
        self.config_path      = config_path
        self.week_index       = config.get("week_index")
        self.folder           = config.get("folder")
        self.filename         = config.get("filename")
        self.lesson_end_time  = config.get("lesson_end_time")
        self.greetings        = config.get("greetings")
        self.day_of_week      = config.get("day_of_week")
        self.lessons_schedule = config.get("lessons_schedule")
        self.bot_token        = config_private.get("bot_token")
        self.db_url           = config_private.get("db_url")
        self.timetable        = dict()
        self.bot              = aiogram.Bot(self.bot_token)
        self.dp               = aiogram.Dispatcher(self.bot)
        self.xls              = XlsHandler("../{}/{}".format(
                                        self.folder,
                                        self.filename
                                    ),
                                    self.day_of_week
                                )
        self.db               = dbHandler(self.db_url)

    ## Core Functions:

    async def get_info(self, message):
        group_bool = message.chat.type != 'private'

        if not message.from_user.username:
            username = "None"
        else:
            username = message.from_user.username

        print(message.from_user.id)
        try:
            print(message.from_user.first_name)
        except Exception:
            print("UNICODE")
        try:
            print(message.from_user.last_name)
        except Exception:
            print("UNICODE")
        if not message.from_user.first_name and not message.from_user.last_name:
            nameofuser = "OH FUCKING SHIET ERR"
        elif not message.from_user.first_name:
            nameofuser = message.from_user.last_name
        elif not message.from_user.last_name:
            nameofuser = message.from_user.first_name
        else:
            nameofuser  = message.from_user.first_name
            nameofuser += ' '
            nameofuser += message.from_user.last_name

        print(1)

        response_arr = self.db.get_info_msgNEW(
            message.from_user.id,
            username,
            nameofuser,
            group_bool,
            message.chat.id,
            message.chat.title
        )

        if not response_arr[0] or self.xls.find_timetable(
            response_arr[0],
            {}
        ) == {}:
            group = "NULL"
        else:
            group = response_arr[0]
            if not self.timetable.get(group):
                self.timetable = self.xls.find_timetable(
                    response_arr[0],
                    self.timetable
                )

        admin_bool = response_arr[1]
        print(2)
        return [
            group,
            admin_bool,
            message.chat.title if group_bool is True else nameofuser
        ]

    def close(self):
        self.db.close()

    ## Message Handling & Responsing Functions

    async def start(self, message):
        response = await self.get_info(message)
        name = response[2]
        await self.bot.send_message(
            message.chat.id,
            self.greetings.format(name),
            parse_mode = 'Markdown'
        )

    async def rozklad(self, message):
        await self.get_info(message)
        new_group = message.text[8:].strip().lower()
        new_group = re.sub('[-]', '', new_group)
        response_message = str()
        if self.xls.find_timetable(new_group, {}) != {}:
            self.db.upd_chat_rozklad(message.chat.id, new_group)
            response_message = "Група була змінена на {}".format(new_group)
        else:
            response_message = "Група не була змінена на {}. Мабуть, її немає в таблиці, чи була допущена помилка, під час її написання.".format(new_group)
        await self.bot.send_message(message.chat.id, response_message)
        print(new_group)

    async def quick_help(self, message):
        await self.get_info(message)
        now = datetime.datetime.now()
        weeknum = 1 if datetime.date(
            now.year,
            now.month,
            now.day
        ).isocalendar()[1] % 2 == self.week_index else 2

        response_message = "*Week: {}* \n/today \t\U00002B50\n/tomorrow \t\U0001F449\n/week \t\U00002B50\n/nextweek \t\U0001F449\n/timetable \t\U0001F6A7\n/left".format(weeknum)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode = 'Markdown'
        )

    async def help(self, message):  #### RUSSISCH LANGUAGE
        response = await self.get_info(message)
        group = response[0]
        now = datetime.datetime.now()
        weeknum = 1 if datetime.date(
            now.year,
            now.month,
            now.day
        ).isocalendar()[1] % 2 == self.week_index else 2

        response_message  = "*{}*\n*Week: {}*".format(group, weeknum)
        response_message += "\nДоступные команды:\n\n/today — расписание на сегодня\n/tomorrow — расписание на завтра\n/week — расписание на неделю\n/nextweek — расписание на следующую неделю\n/timetable — расписание звонков\n\n/full — расписание на две недели\n/left — показывает время до конца пары\n/currentLesson — информация о текущей паре\n/nextLesson — информация о следующей паре\n\n/rozklad НАЗВАНИЕГРУППЫ - показать расписание для другой группы\n /find\_info ЗАПИТ — пошук пар, за запитом (кабінет, фамілія вмкладача, назва предмету, тощо). Наприклад: `/find_info Яковлєв`\n\n/quickhelp — быстрый список команд\n/help — показать это сообщение \U0001F631"
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode = 'Markdown'
        )

    async def today(self, message):
        response = await self.get_info(message)
        group = response[0]

        if len(message.text) > message.entities[0].length:
            group_arr = await self.get_group_from_message(
                message.text[message.entities[0].length:].strip()
            )
            if group_arr[0] is False:
                await self.bot.send_message(
                    message.chat.id,
                    group_arr[1],
                    parse_mode = 'Markdown'
                )
                return
            group = group_arr[1]

        if group == "NULL":
            await self.bot.send_message(
                message.chat.id,
                "Ваша поточна група: ***NULL***\nСпробуйте додати групу наприкінці запросу. Наприклад: `/today фі-73` \nАбо задайте групу таким чином: `/rozklad фі-73`",
                parse_mode = 'Markdown'
            )
            return

        name = response[2]
        response_message = await self.today_mes(group, name)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode = 'Markdown'
        )

    async def tomorrow(self, message):
        response = await self.get_info(message)
        group = response[0]

        if len(message.text) > message.entities[0].length:
            group_arr = await self.get_group_from_message(
                message.text[message.entities[0].length:].strip()
            )
            if group_arr[0] is False:
                await self.bot.send_message(
                    message.chat.id,
                    group_arr[1],
                    parse_mode = 'Markdown'
                )
                return
            group = group_arr[1]

        if group == "NULL":
            await self.bot.send_message(
                message.chat.id,
                "Ваша поточна група: ***NULL***\nСпробуйте додати групу наприкінці запросу. Наприклад: `/tomorrow фі-73` \nАбо задайте групу таким чином: `/rozklad фі-73`",
                parse_mode = 'Markdown'
            )
            return

        name = response[2]
        response_message = await self.tomorrow_mes(group, name)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode = 'Markdown'
        )

    async def week(self, message):
        response = await self.get_info(message)
        group = response[0]

        if len(message.text) > message.entities[0].length:
            group_arr = await self.get_group_from_message(
                message.text[message.entities[0].length:].strip()
            )
            if group_arr[0] is False:
                await self.bot.send_message(
                    message.chat.id,
                    group_arr[1],
                    parse_mode = 'Markdown'
                )
                return
            group = group_arr[1]

        if group == "NULL":
            await self.bot.send_message(
                message.chat.id,
                "Ваша поточна група: ***NULL***\nСпробуйте додати групу наприкінці запросу. Наприклад: `/week фі-73` \nАбо задайте групу таким чином: `/rozklad фі-73`",
                parse_mode = 'Markdown'
            )
            return

        response_message = await self.week_mes(group)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode = 'Markdown'
        )

    async def next_week(self, message):
        response = await self.get_info(message)
        group = response[0]

        if len(message.text) > message.entities[0].length:
            group_arr = await self.get_group_from_message(
                message.text[message.entities[0].length:].strip()
            )
            if group_arr[0] is False:
                await self.bot.send_message(
                    message.chat.id,
                    group_arr[1],
                    parse_mode = 'Markdown'
                )
                return
            group = group_arr[1]

        if group == "NULL":
            await self.bot.send_message(
                message.chat.id,
                "Ваша поточна група: ***NULL***\nСпробуйте додати групу наприкінці запросу. Наприклад: `/nextweek фі-73` \nАбо задайте групу таким чином: `/rozklad фі-73`",
                parse_mode = 'Markdown'
            )
            return

        response_message = await self.next_week_mes(group)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode = 'Markdown'
        )

    async def full(self, message):
        response = await self.get_info(message)
        group = response[0]

        if len(message.text) > message.entities[0].length:
            group_arr = await self.get_group_from_message(
                message.text[message.entities[0].length:].strip()
            )
            if group_arr[0] is False:
                await self.bot.send_message(
                    message.chat.id,
                    group_arr[1],
                    parse_mode = 'Markdown'
                )
                return
            group = group_arr[1]

        if group == "NULL":
            await self.bot.send_message(
                message.chat.id,
                "Ваша поточна група: ***NULL***\nСпробуйте додати групу наприкінці запросу. Наприклад: `/full фі-73` \nАбо задайте групу таким чином: `/rozklad фі-73`",
                parse_mode = 'Markdown'
            )
            return

        response_message = await self.full_mes(group)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode = 'Markdown'
        )

    async def current_lesson(self, message):
        response = await self.get_info(message)
        group = response[0]

        if len(message.text) > message.entities[0].length:
            group_arr = await self.get_group_from_message(
                message.text[message.entities[0].length:].strip()
            )
            if group_arr[0] is False:
                await self.bot.send_message(
                    message.chat.id,
                    group_arr[1],
                    parse_mode = 'Markdown'
                )
                return
            group = group_arr[1]

        if group == "NULL":
            await self.bot.send_message(
                message.chat.id,
                "Ваша поточна група: ***NULL***\nСпробуйте додати групу наприкінці запросу. Наприклад: `/currentlesson фі-73` \nАбо задайте групу таким чином: `/rozklad фі-73`",
                parse_mode = 'Markdown'
            )
            return

        name = response[2]
        response_message = await self.current_lesson_mes(group, name)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode = 'Markdown'
        )

    async def next_lesson(self, message):
        response = await self.get_info(message)
        group = response[0]

        if len(message.text) > message.entities[0].length:
            group_arr = await self.get_group_from_message(
                message.text[message.entities[0].length:].strip()
            )
            if group_arr[0] is False:
                await self.bot.send_message(
                    message.chat.id,
                    group_arr[1],
                    parse_mode = 'Markdown'
                )
                return
            group = group_arr[1]

        if group == "NULL":
            await self.bot.send_message(
                message.chat.id,
                "Ваша поточна група: ***NULL***\nСпробуйте додати групу наприкінці запросу. Наприклад: `/nextlesson фі-73` \nАбо задайте групу таким чином: `/rozklad фі-73`",
                parse_mode = 'Markdown'
            )
            return

        name = response[2]
        response_message = await self.next_lesson_mes(group, name)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode = 'Markdown'
        )

    async def timetable_MES(self, message):
        await self.get_info(message)
        await self.bot.send_message(
            message.chat.id,
            self.lessons_schedule,
            parse_mode = 'Markdown'
        )

    async def left(self, message):
        response = await self.get_info(message)
        name = response[2]
        response_message = await self.left_mes(name)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode = 'Markdown'
        )

    async def find_info(self, message): ## ENGLISH LANGUAGE
        await self.get_info(message)
        response_message = self.xls.find_info(
            message.text[message.entities[0].length:].strip()
        )
        try:
            await self.bot.send_message(
                message.chat.id,
                response_message,
                parse_mode = 'Markdown'
            )
        except Exception:
            await self.bot.send_message(
                message.chat.id,
                "Err in message.\nMaybe it is too long or has a bad request.",
                parse_mode='Markdown'
            )

    async def change_week(self, message):
        response   = await self.get_info(message)
        admin_bool = response[1]
        if admin_bool is True:
            await self.bot.send_message(message.chat.id, "ADMIN MODE")
            #
            # LOG THIS ACTION!
            #
            self.week_index = 1 if self.week_index == 0 else 0
            await self.change_week_json()
            await self.bot.send_message(
                message.chat.id,
                "Week_index successfully has been changed"
            )
        else:
            await self.bot.send_message(
                message.chat.id,
                "You are not admin, get out of here!"
            )

    async def update_file(self, message):
        response = await self.get_info(message)
        admin_bool = response[1]
        if admin_bool is True:
            await self.bot.send_message(
                message.chat.id,
                "ADMIN MODE",
                parse_mode = 'Markdown'
            )
            url     = message.text[message.entities[0].length:].strip()
            request = requests.get(url)
            #
            # LOG THIS ACTION!
            #
            if request.status_code == 200 and request.headers["Content-Type"] == "application/vnd.ms-excel":
                with open(
                    "../{}/{}".format(self.folder, self.filename),
                    'wb'
                ) as update_file:
                    update_file.write(request.content)
                self.timetable.clear()
                self.xls.update("../{}/{}".format(self.folder, self.filename))
                response_message = "<b>Увага!</b>\nРозклад було оновлено.\n<a href=\"{}\">Посилання на новий файл</a>".format(url)
                await self.send_everyone(response_message, 'HTML')
            else:
                await self.bot.send_message(
                    message.chat.id,
                    "URL error (not 200 code or wrong type must be: \"application/vnd.ms-excel\")",
                    parse_mode='Markdown'
                )
        else:
            await self.bot.send_message(
                message.chat.id,
                "You are not admin, get out of here!",
                parse_mode='Markdown'
            )

    ## Secondary Additional Functions:

    async def get_group_from_message(self, message):
        group = re.sub('[-]', '', message)
        if self.timetable.get(group):
            return [True, group]
        elif self.xls.find_timetable(group, {}) != {}:
            self.timetable = self.xls.find_timetable(group, self.timetable)
            return [True, group]
        else:
            return [
                False,
                "Група не була знайдена. Мабуть, її немає в таблиці, чи була допущена помилка, під час її написання."
            ]

    async def change_week_json(self):
        with open(self.config_path, encoding = 'utf-8') as json_file:
            config = json.load(json_file)
        config["week_index"] = self.week_index
        with open(self.config_path, 'w', encoding = 'utf-8') as json_outfile:
            json.dump(config, json_outfile, indent = 4)

    async def send_everyone(self, response_message, parse_mode):
        chat_ids = self.db.get_chatIds()
        deleted_chats = list()
        for elem in chat_ids:
            try:
                await self.bot.send_message(
                    elem[0],
                    response_message,
                    parse_mode = parse_mode
                )
            except aiogram.utils.exceptions.ChatNotFound:
                deleted_chats.append(elem[0])
        '''
        if len(deleted_chats) > 0:
            self.db.delete_chats(deleted_chats)
        '''

    ## Main Additional Functions:

    async def today_mes(self, group, name):
        today = datetime.datetime.today()
        weeknum = 1 if datetime.date(
            today.year,
            today.month,
            today.day
        ).isocalendar()[1] % 2 == self.week_index else 2

        weekday = today.weekday() + 1

        if weekday == 7:
            today_res = "Сьогодні ж *НЕДІЛЯ*! {}".format(name)

        else:
            day_temp = (
                self.xls.get_day_timetable(
                    group,
                    self.timetable,
                    weekday,
                    weeknum
                )
            )[:-1]

            ### DELETING EMPTY LESSONS ###

            for del_str in range(5, 0, -1):
                if day_temp.rfind("_----_") == len(day_temp) - 6:
                    day_temp = day_temp[:(
                        day_temp.rfind("*{})*".format(del_str))
                    ) - 1]

                ### DELETING EMPTY DAYS ###

            if get_key(
                self.day_of_week,
                re.sub(r'[*-: \n ]', "", day_temp)
            ) == -1:
                today_res = day_temp
            else:
                today_res  = day_temp
                today_res += "\nСьогодні в тебе *нічого* немає, відпочивай"

        return today_res

    async def tomorrow_mes(self, group, name):
        tomorrow = datetime.date.today() + datetime.timedelta(days = 1)
        weeknum = 1 if datetime.date(
            tomorrow.year,
            tomorrow.month,
            tomorrow.day + 1
        ).isocalendar()[1] % 2 == self.week_index else 2

        weekday = tomorrow.weekday() + 1

        if weekday == 7:
            tomorrow_res = "Завтра *НЕДІЛЯ*! {}".format(name)

        else:
            day_temp = (
                self.xls.get_day_timetable(
                    group,
                    self.timetable,
                    weekday,
                    weeknum
                )
            )[:-1]

            ### DELETING EMPTY LESSONS ###

            for del_str in range(5, 0, -1):
                if day_temp.rfind("_----_") == len(day_temp) - 6:
                    day_temp = day_temp[:(
                        day_temp.rfind("*{})*".format(del_str))
                    ) - 1]

                ### DELETING EMPTY DAYS ###

            if get_key(
                self.day_of_week,
                re.sub(r'[*-: \n ]', "", day_temp)
            ) == -1:
                tomorrow_res = day_temp
            else:
                tomorrow_res  = day_temp
                tomorrow_res += "\nЗавтра в тебе *нічого* не буде, відпочивай"

        return tomorrow_res

    async def week_mes(self, group):
        today = datetime.datetime.today()
        weeknum = 1 if datetime.date(
            today.year,
            today.month,
            today.day
        ).isocalendar()[1] % 2 == self.week_index else 2

        week_res = self.xls.get_week_timetable(
            group,
            self.timetable,
            weeknum
        )
        return week_res

    async def next_week_mes(self, group):
        today = datetime.datetime.today()
        weeknum = 2 if datetime.date(
            today.year,
            today.month,
            today.day
        ).isocalendar()[1] % 2 == self.week_index else 1

        next_week_res = self.xls.get_week_timetable(
            group,
            self.timetable,
            weeknum
        )
        return next_week_res

    async def full_mes(self, group):
        week_res  = self.xls.get_week_timetable(group, self.timetable, 1)
        week_res += "\n" * 2
        week_res += self.xls.get_week_timetable(group, self.timetable, 2)
        return week_res

    async def current_lesson_mes(self, group, name):  # RUSSISCH LANGUAGE
        now = datetime.datetime.now()
        weeknum = 1 if datetime.date(
            now.year,
            now.month,
            now.day
        ).isocalendar()[1] % 2 == self.week_index else 2

        weekday = now.weekday() + 1

        if weekday == 7:
            result = "Сьогодні ж *НЕДІЛЯ*! {}".format(name)
            return result

        result = "Сьогодні пар більше не буде, бо вже вечір\n/nextlesson — покаже тобі інформацію про наступну пару".format(name)

        now = now.strftime('%X')  # Get time like string HH:MM:SS
        FMT1 = '%H:%M:%S'
        FMT2 = '%H:%M'

        try:
            for i in range(len(self.lesson_end_time)):
                tdelta = datetime.datetime.strptime(
                    self.lesson_end_time[i],
                    FMT2
                ) - datetime.datetime.strptime(
                    now,
                    FMT1
                )

                if tdelta.days == 0:
                    delta_minutes = tdelta.seconds // 60
                    delta_seconds = tdelta.seconds % 60
                    if delta_minutes > 94:
                        result = "Погоди, все ещё идет перемена (или же сейчас утро), *{}*, отдыхай\n/nextLesson — покажет тебе информацию о следующей паре".format(name)
                        return result
                    curr_lesson = self.xls.get_current_lesson(
                        group,
                        self.timetable,
                        weekday,
                        weeknum,
                        i + 1
                    )
                    result  = "Сейчас идет _{} пара_:\n".format(i + 1)
                    result += curr_lesson
                    result += "\nДо конца этой пары: *{} мин {} сек*".format(
                        delta_minutes,
                        delta_seconds
                    )
                    if curr_lesson == '':
                        result = "Сейчас идет _{} пара_:\nНо у тебя на ней *ничего* нет :)\n------------------------------\nВремя до конца этой пары: *{} мин {} сек*\n------------------------------\n/nextLesson — покажет тебе информацию о следующей паре".format(i + 1, delta_minutes, delta_seconds)
                    return result
        except Exception as e:
            print(e)
            result = "Произошла ошибка, извините...".format(name)
        return result

    async def next_lesson_mes(self, group, name):  # RUSSISCH LANGUAGE
        now = datetime.datetime.now()

        weeknum = 1 if datetime.date(
            now.year,
            now.month,
            now.day
        ).isocalendar()[1] % 2 == self.week_index else 2
        result  = str()
        weekday = now.weekday() + 1

        now = now.strftime('%X')

        FMT1 = '%H:%M:%S'
        FMT2 = '%H:%M'

        add_days = 0

        try:
            while True:
                for i in range(len(self.lesson_end_time)):
                    tdelta = datetime.datetime.strptime(
                        self.lesson_end_time[i],
                        FMT2
                    ) - datetime.datetime.strptime(
                        now,
                        FMT1
                    )
                    if add_days == 0:
                        if tdelta.days == 0:
                            delta_minutes = tdelta.seconds // 60
                            delta_seconds = tdelta.seconds % 60
                            if delta_minutes < 95:
                                continue
                            next_lesson = self.xls.get_current_lesson(
                                group,
                                self.timetable,
                                weekday,
                                weeknum,
                                i + 1
                            )
                            if next_lesson == '':
                                continue
                            result  = "Следующая будет _{} пара_:\n".format(i + 1)
                            result += next_lesson
                            result += "\nЧерез *{} мин {} сек*".format(
                                delta_minutes - 95,
                                delta_seconds
                            )
                            return result
                    else:
                        delta_minutes  = tdelta.seconds // 60 - 95
                        delta_hours    = delta_minutes // 60 % 24
                        delta_minutes %= 60
                        next_lesson = self.xls.get_current_lesson(
                            group,
                            self.timetable,
                            weekday,
                            weeknum,
                            i + 1
                        )
                        if next_lesson == '':
                            continue
                        result  = "Следующая будет _{} пара_ в *{} {}*:\n".format(
                            i + 1,
                            self.day_of_week[str(weekday)],
                            weeknum
                        )
                        result += next_lesson
                        result += "\nЧерез: *{} дн {} год {} хв*".format(
                            tdelta.days + add_days,
                            delta_hours,
                            delta_minutes
                        )
                        return result
                weekday  += 1
                add_days += 1
                if weekday == 7:
                    weekday = 1
                    weeknum = 1 if weeknum == 2 else 2
        except Exception as e:
            print(e)
            result = "Произошла ошибка, извините...".format(name)
        return result

    async def left_mes(self, name):  # RUSSISCH LANGUAGE
        now = datetime.datetime.now()

        left_result = "Не могу посчитать время... \n*{}*, а сейчас точно пара?".format(name)
        now = now.strftime('%X')
        FMT1 = '%H:%M:%S'
        FMT2 = '%H:%M'
        try:
            for i in range(len(self.lesson_end_time)):
                tdelta = datetime.datetime.strptime(
                    self.lesson_end_time[i],
                    FMT2
                ) - datetime.datetime.strptime(
                    now,
                    FMT1
                )
                if tdelta.days == 0:
                    delta_minutes = tdelta.seconds // 60
                    delta_seconds = tdelta.seconds % 60
                    if delta_minutes > 94:
                        left_result  = "Перемена еще не закончилась.\nДо начала следующей _({} пары)_".format(i + 1)
                        left_result += " осталось: *{} ".format(delta_minutes - 95)
                        left_result += "мин {} сек*".format(delta_seconds)
                    else:
                        left_result  = "До конца {}".format(i + 1)
                        left_result += " пары осталось: *{} ".format(delta_minutes)
                        left_result += "мин {} сек*".format(delta_seconds)
                    return left_result
        except Exception as e:
            print(e)
            left_result = "Не могу посчитать время... \n*{}*, а сейчас точно пара?".format(name)
        return left_result

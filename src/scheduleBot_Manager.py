import json
import aiogram
import re
import datetime
import pytz
import requests
from xls_handler import XlsHandler
from xls_handler import get_key
from db_handler import dbHandler


class ScheduleBot_Manager:
    def __init__(self, config_path, config_private_path):
        with open(config_path, encoding='utf-8') as json_file:
            config = json.load(json_file)
        with open(config_private_path, encoding='utf-8') as json_file:
            config_private = json.load(json_file)
        self.config_path      = config_path
        self.time_zone        = config.get("time_zone")
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
        xls_path              = f"../{self.folder}/{self.filename}"
        self.xls              = XlsHandler(xls_path, self.day_of_week)
        self.db               = dbHandler(self.db_url)
        self.UA_tz            = pytz.timezone(self.time_zone)

    # Core Functions:

    async def get_info(self, message):
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
        last_name  = message.from_user.last_name
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

        xls_response = self.xls.find_timetable(response_arr[0], dict())
        if not response_arr[0] or xls_response == dict():
            group = "NULL"
        else:
            group = response_arr[0]
            if not self.timetable.get(group):
                self.timetable = self.xls.find_timetable(
                    response_arr[0],
                    self.timetable
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

    # Message Handling & Responsing Functions

    async def start(self, message):
        response = await self.get_info(message)
        name = response[2]
        await self.bot.send_message(
            message.chat.id,
            self.greetings.format(name),
            parse_mode='Markdown'
        )

    async def rozklad(self, message):
        await self.get_info(message)
        new_group = message.text[8:].strip().lower()
        new_group = re.sub('[-]', '', new_group)
        response_message = str()
        if self.xls.find_timetable(new_group, dict()) != dict():
            self.db.upd_chat_rozklad(message.chat.id, new_group)
            response_message = f"Група була змінена на {new_group}"
        else:
            response_message = f"Група не була змінена на {new_group}. " \
                               f"Мабуть, її немає в таблиці, чи була " \
                               f"допущена помилка, під час її написання."
        await self.bot.send_message(message.chat.id, response_message)
        print(new_group)

    async def quick_help(self, message):
        await self.get_info(message)
        weeknum = await self.get_current_week()

        response_message = f"*Week: {weeknum}* \n" \
                           f"/today \t\U00002B50\n" \
                           f"/tomorrow \t\U0001F449\n" \
                           f"/week \t\U00002B50\n" \
                           f"/nextweek \t\U0001F449\n" \
                           f"/timetable \t\U0001F6A7\n" \
                           f"/left"
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def help(self, message):  # RUSSISCH LANGUAGE
        response = await self.get_info(message)
        group = response[0]
        weeknum = await self.get_current_week()

        response_message = f"*{group}*\n*Week: {weeknum}*\n" \
                           f"Доступные команды:\n\n" \
                           f"/today — расписание на сегодня\n" \
                           f"/tomorrow — расписание на завтра\n" \
                           f"/week — расписание на неделю\n" \
                           f"/nextweek — расписание на следующую неделю\n" \
                           f"/timetable — расписание звонков\n\n" \
                           f"/full — расписание на две недели\n" \
                           f"/left — показывает время до конца пары\n" \
                           f"/currentLesson — информация о текущей паре\n" \
                           f"/nextLesson — информация о следующей паре\n\n" \
                           f"/rozklad НАЗВАНИЕГРУППЫ - показать расписание" \
                           f"для другой группы\n" \
                           f"/find\_info ЗАПИТ — пошук пар, за запитом " \
                           f"(кабінет, фамілія вмкладача, назва предмету," \
                           f"тощо). Наприклад: `/find_info Яковлєв`\n\n" \
                           f"/quickhelp — быстрый список команд\n" \
                           f"/help — показать это сообщение \U0001F631"
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
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
                    parse_mode='Markdown'
                )
                return
            group = group_arr[1]

        if group == "NULL":
            response_message = f"Ваша поточна група: ***NULL***\n" \
                               f"Спробуйте додати групу наприкінці запросу. " \
                               f"Наприклад: `/today фі-73` \n" \
                               f"Або задайте групу таким чином: " \
                               f"`/rozklad фі-73`"
            await self.bot.send_message(
                message.chat.id,
                response_message,
                parse_mode='Markdown'
            )
            return

        name = response[2]
        response_message = await self.today_mes(group, name)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
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
                    parse_mode='Markdown'
                )
                return
            group = group_arr[1]

        if group == "NULL":
            response_message = f"Ваша поточна група: ***NULL***\n" \
                               f"Спробуйте додати групу наприкінці запросу. " \
                               f"Наприклад: `/tomorrow фі-73` \n" \
                               f"Або задайте групу таким чином: " \
                               f"`/rozklad фі-73`"
            await self.bot.send_message(
                message.chat.id,
                response_message,
                parse_mode='Markdown'
            )
            return

        name = response[2]
        response_message = await self.tomorrow_mes(group, name)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
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
                    parse_mode='Markdown'
                )
                return
            group = group_arr[1]

        if group == "NULL":
            response_message = f"Ваша поточна група: ***NULL***\n" \
                               f"Спробуйте додати групу наприкінці запросу. " \
                               f"Наприклад: `/week фі-73` \n" \
                               f"Або задайте групу таким чином: " \
                               f"`/rozklad фі-73`"
            await self.bot.send_message(
                message.chat.id,
                response_message,
                parse_mode='Markdown'
            )
            return

        response_message = await self.week_mes(group)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
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
                    parse_mode='Markdown'
                )
                return
            group = group_arr[1]

        if group == "NULL":
            response_message = f"Ваша поточна група: ***NULL***\n" \
                               f"Спробуйте додати групу наприкінці запросу. " \
                               f"Наприклад: `/next_week фі-73` \n" \
                               f"Або задайте групу таким чином: " \
                               f"`/rozklad фі-73`"
            await self.bot.send_message(
                message.chat.id,
                response_message,
                parse_mode='Markdown'
            )
            return

        response_message = await self.next_week_mes(group)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
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
                    parse_mode='Markdown'
                )
                return
            group = group_arr[1]

        if group == "NULL":
            response_message = f"Ваша поточна група: ***NULL***\n" \
                               f"Спробуйте додати групу наприкінці запросу. " \
                               f"Наприклад: `/full фі-73` \n" \
                               f"Або задайте групу таким чином: " \
                               f"`/rozklad фі-73`"
            await self.bot.send_message(
                message.chat.id,
                response_message,
                parse_mode='Markdown'
            )
            return

        response_message = await self.full_mes(group)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
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
                    parse_mode='Markdown'
                )
                return
            group = group_arr[1]

        if group == "NULL":
            response_message = f"Ваша поточна група: ***NULL***\n" \
                               f"Спробуйте додати групу наприкінці запросу. " \
                               f"Наприклад: `/currentlesson фі-73` \n" \
                               f"Або задайте групу таким чином: " \
                               f"`/rozklad фі-73`"
            await self.bot.send_message(
                message.chat.id,
                response_message,
                parse_mode='Markdown'
            )
            return

        name = response[2]
        response_message = await self.current_lesson_mes(group, name)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
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
                    parse_mode='Markdown'
                )
                return
            group = group_arr[1]

        if group == "NULL":
            response_message = f"Ваша поточна група: ***NULL***\n" \
                               f"Спробуйте додати групу наприкінці запросу. " \
                               f"Наприклад: `/nextlesson фі-73` \n" \
                               f"Або задайте групу таким чином: " \
                               f"`/rozklad фі-73`"
            await self.bot.send_message(
                message.chat.id,
                response_message,
                parse_mode='Markdown'
            )
            return

        name = response[2]
        response_message = await self.next_lesson_mes(group, name)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def timetable_MES(self, message):
        await self.get_info(message)
        await self.bot.send_message(
            message.chat.id,
            self.lessons_schedule,
            parse_mode='Markdown'
        )

    async def left(self, message):
        response = await self.get_info(message)
        name = response[2]
        response_message = await self.left_mes(name)
        await self.bot.send_message(
            message.chat.id,
            response_message,
            parse_mode='Markdown'
        )

    async def find_info(self, message):  # ENGLISH LANGUAGE
        await self.get_info(message)
        response_message = self.xls.find_info(
            message.text[message.entities[0].length:].strip()
        )
        try:
            await self.bot.send_message(
                message.chat.id,
                response_message,
                parse_mode='Markdown'
            )
        except Exception:
            response_message = f"Err in message.\n" \
                               f"Maybe it is too long or has a bad request."
            await self.bot.send_message(
                message.chat.id,
                response_message,
                parse_mode='Markdown'
            )

    async def change_week(self, message):
        response = await self.get_info(message)
        admin_bool = response[1]
        if admin_bool is True:
            await self.bot.send_message(message.chat.id, "ADMIN MODE")
            #
            # LOG THIS ACTION!
            #
            self.week_index = 1 if self.week_index == 0 else 0
            await self.change_week_json()
            response_message = "Week_index successfully has been changed"
            await self.bot.send_message(message.chat.id, response_message)
        else:
            response_message = "You are not admin, get out of here!"
            await self.bot.send_message(message.chat.id, response_message)

    async def update_file(self, message):
        response = await self.get_info(message)
        admin_bool = response[1]
        if admin_bool is True:
            response_message = "ADMIN MODE"
            await self.bot.send_message(message.chat.id, response_message)
            url = message.text[message.entities[0].length:].strip()
            request = requests.get(url)
            req_code = request.status_code
            req_type = request.headers["Content-Type"]
            #
            # LOG THIS ACTION!
            #
            if req_code == 200 and req_type == "application/vnd.ms-excel":
                with open(
                    f"../{self.folder}/{self.filename}",
                    'wb'
                ) as update_file:
                    update_file.write(request.content)
                self.timetable.clear()
                self.xls.update(f"../{self.folder}/{self.filename}")
                response_message = f"<b>Увага!</b>\n" \
                                   f"Розклад було оновлено.\n" \
                                   f"<a href=\"{url}\">" \
                                   f"Посилання на новий файл</a>"
                await self.send_everyone(response_message, 'HTML')
            else:
                response_message = f"URL error (not 200 code or wrong type" \
                                   f" must be: \"application/vnd.ms-excel\")"
                await self.bot.send_message(message.chat.id, response_message)
        else:
            response_message = "You are not admin, get out of here!"
            await self.bot.send_message(message.chat.id, response_message)

    # Main Additional Functions:

    async def today_mes(self, group, name):
        today = datetime.datetime.now(self.UA_tz)
        weeknum = await self.get_current_week(today)

        weekday = today.weekday() + 1

        if weekday == 7:
            today_res = f"Сьогодні ж *НЕДІЛЯ*! {name}"

        else:
            day_temp = self.xls.get_day_timetable(
                group,
                self.timetable,
                weekday,
                weeknum
            )
            day_temp = day_temp[:-1]

            # DELETING EMPTY LESSONS

            for del_str in range(5, 0, -1):
                if day_temp.rfind("_----_") == len(day_temp) - 6:
                    cut_index = day_temp.rfind(f"*{del_str})*") - 1
                    day_temp = day_temp[:cut_index]

                # DELETING EMPTY DAYS

            get_key_result = get_key(
                self.day_of_week,
                re.sub(r'[*-: \n ]', "", day_temp)
            )

            if get_key_result == -1:
                today_res = day_temp
            else:
                today_res = day_temp
                today_res += "\nСьогодні в тебе *нічого* немає, відпочивай"

        return today_res

    async def tomorrow_mes(self, group, name):
        tomorrow = datetime.date.now(self.UA_tz) + datetime.timedelta(days=1)
        weeknum = await self.get_current_week(tomorrow)

        weekday = tomorrow.weekday() + 1

        if weekday == 7:
            tomorrow_res = f"Завтра *НЕДІЛЯ*! {name}"

        else:
            day_temp = (self.xls.get_day_timetable(
                group,
                self.timetable,
                weekday,
                weeknum
            ))
            day_temp = day_temp[:-1]

            # DELETING EMPTY LESSONS

            for del_str in range(5, 0, -1):
                if day_temp.rfind("_----_") == len(day_temp) - 6:
                    cut_index = day_temp.rfind("*{del_str})*") - 1
                    day_temp = day_temp[:cut_index]

                # DELETING EMPTY DAYS

            get_key_result = get_key(
                self.day_of_week,
                re.sub(r'[*-: \n ]', "", day_temp)
            )
            if get_key_result == -1:
                tomorrow_res = day_temp
            else:
                tomorrow_res = day_temp
                tomorrow_res += "\nЗавтра в тебе *нічого* не буде, відпочивай"

        return tomorrow_res

    async def week_mes(self, group):
        today = datetime.datetime.now(self.UA_tz)
        weeknum = await self.get_current_week(today)

        week_res = self.xls.get_week_timetable(
            group,
            self.timetable,
            weeknum
        )
        return week_res

    async def next_week_mes(self, group):
        today = datetime.datetime.now(self.UA_tz)
        weeknum = 2 if await self.get_current_week(today) == 1 else 1

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
        now = datetime.datetime.now(self.UA_tz)
        weeknum = await self.get_current_week(now)

        weekday = now.weekday() + 1

        if weekday == 7:
            result = f"Сьогодні ж *НЕДІЛЯ*! {name}"
            return result

        result = f"Сьогодні пар більше не буде, бо вже вечір\n" \
                 f"/nextlesson — покаже тобі інформацію про наступну пару"

        now = now.strftime('%X')  # Get time like string HH:MM:SS

        FMT1 = '%H:%M:%S'
        FMT2 = '%H:%M'

        current_point = datetime.datetime.strptime(now, FMT1)
        try:
            for i in range(len(self.lesson_end_time)):
                lesson_end_point = datetime.datetime.strptime(
                    self.lesson_end_time[i],
                    FMT2
                )
                tdelta = lesson_end_point - current_point

                if tdelta.days == 0:
                    delta_minutes = tdelta.seconds // 60
                    delta_seconds = tdelta.seconds % 60
                    if delta_minutes > 94:
                        result = f"Погоди, все ещё идет перемена (или же " \
                                 f"сейчас утро), *{name}*, отдыхай\n" \
                                 f"/nextLesson — покажет тебе информацию " \
                                 f"о следующей паре"
                        return result
                    curr_lesson = self.xls.get_current_lesson(
                        group,
                        self.timetable,
                        weekday,
                        weeknum,
                        i + 1
                    )
                    result  = f"Сейчас идет _{i + 1} пара_:\n"
                    result += curr_lesson
                    result += f"\nДо конца этой пары: *{delta_minutes} мин" \
                              f"{delta_seconds} сек*"
                    if curr_lesson == '':
                        result = f"Сейчас идет _{i + 1} пара_:\nНо у тебя на" \
                                 f" ней *ничего* нет :)\n" \
                                 f"------------------------------\n" \
                                 f"Время до конца этой пары: " \
                                 f"*{delta_minutes} мин {delta_seconds} " \
                                 f"сек*\n" \
                                 f"------------------------------\n" \
                                 f"/nextLesson — покажет тебе информацию " \
                                 f"о следующей паре"
                    return result
        except Exception as e:
            print(e)
            result = f"Произошла ошибка, извините..."
        return result

    async def next_lesson_mes(self, group, name):  # RUSSISCH LANGUAGE
        now = datetime.datetime.now(self.UA_tz)
        weeknum = await self.get_current_week(now)

        result = str()
        weekday = now.weekday() + 1

        now = now.strftime('%X')

        FMT1 = '%H:%M:%S'
        FMT2 = '%H:%M'

        current_point = datetime.datetime.strptime(now, FMT1)

        add_days = 0
        try:
            while True:
                for i in range(len(self.lesson_end_time)):
                    lesson_end_point = datetime.datetime.strptime(
                        self.lesson_end_time[i],
                        FMT2
                    )
                    tdelta = lesson_end_point - current_point

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
                            result  = f"Следующая будет _{i + 1} пара_:\n"
                            result += next_lesson
                            result += f"\nЧерез *{delta_minutes - 95} мин " \
                                      f"{delta_seconds} сек*"
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
                        result  = f"Следующая будет _{i + 1} пара_ в " \
                                  f"*{self.day_of_week[str(weekday)]} " \
                                  f"{weeknum}*:\n"
                        result += next_lesson
                        result += f"\nЧерез: *{tdelta.days + add_days} дн " \
                                  f"{delta_hours} год {delta_minutes} хв*"
                        return result

                # начинаем проходить каждый день,
                # пока не попадем на пару,
                # а не на окна (пустые пары)

                weekday  += 1
                add_days += 1

                # если попало на воскресенье, то мы автоматом
                # переключаемся с него на понедельник

                if weekday == 7:
                    add_days += 1
                    weekday = 1
                    weeknum = 1 if weeknum == 2 else 2
        except Exception as e:
            print(e)
            result = f"Произошла ошибка, извините..."
        return result

    async def left_mes(self, name):  # RUSSISCH LANGUAGE
        now = datetime.datetime.now(self.UA_tz)

        left_result = f"Не могу посчитать время... \n*{name}*, " \
                      f"а сейчас точно пара?"
        now = now.strftime('%X')
        FMT1 = '%H:%M:%S'
        FMT2 = '%H:%M'
        current_point = datetime.datetime.strptime(now, FMT1)
        try:
            for i in range(len(self.lesson_end_time)):
                lesson_end_point = datetime.datetime.strptime(
                    self.lesson_end_time[i],
                    FMT2
                )
                tdelta = lesson_end_point - current_point

                if tdelta.days == 0:
                    delta_minutes = tdelta.seconds // 60
                    delta_seconds = tdelta.seconds % 60
                    if delta_minutes > 94:
                        left_result  = f"Перемена еще не закончилась.\n" \
                                       f"До начала следующей _({i + 1} пары)" \
                                       f"_ осталось: *{delta_minutes - 95} " \
                                       f"мин {delta_seconds} сек*"
                    else:
                        left_result  = f"До конца {i + 1}" \
                                       f" пары осталось: *{delta_minutes} " \
                                       f"мин {delta_seconds} сек*"
                    return left_result
        except Exception as e:
            print(e)
            left_result = f"Не могу посчитать время... \n*{name}*, " \
                          f"а сейчас точно пара?"
        return left_result

    # Secondary Additional Functions:

    async def get_group_from_message(self, message):
        group = re.sub('[-]', '', message)
        if self.timetable.get(group):
            return [True, group]
        elif self.xls.find_timetable(group, dict()) != dict():
            self.timetable = self.xls.find_timetable(group, self.timetable)
            return [True, group]
        else:
            return [
                False,
                f"Група не була знайдена. Мабуть, її немає в таблиці, "
                f"чи була допущена помилка, під час її написання."
            ]

    async def change_week_json(self):
        with open(self.config_path, encoding='utf-8') as json_file:
            config = json.load(json_file)
        config["week_index"] = self.week_index
        with open(self.config_path, 'w', encoding='utf-8') as json_outfile:
            json.dump(config, json_outfile, indent=4)

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

    async def get_current_week(self, time=None):
        if not time:
            time = datetime.datetime.now(self.UA_tz)
        weeknum = datetime.date(
            time.year,
            time.month,
            time.day
        ).isocalendar()[1]
        return 1 if weeknum % 2 == self.week_index else 2

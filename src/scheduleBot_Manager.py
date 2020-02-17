import re
import requests
import datetime
import json
import pytz
from xls_handler import XlsHandler
from xls_handler import get_key


class ScheduleBotManager:
    def __init__(self, curr_path, config_path):
        with open(curr_path + config_path, encoding='utf-8') as json_file:
            config = json.load(json_file)
        self.curr_path = curr_path
        self.config_path = config_path
        self.time_zone = config.get("time_zone")
        self.week_index = config.get("week_index")
        self.folder = config.get("folder")
        self.filename = config.get("filename")
        self.lesson_end_time = config.get("lesson_end_time")
        self.greetings = config.get("greetings")
        self.day_of_week = config.get("day_of_week")
        self.lessons_schedule = config.get("lessons_schedule")
        self.timetable = dict()
        xls_path = f"{self.curr_path}../{self.folder}/{self.filename}"
        self.xls = XlsHandler(xls_path, self.day_of_week)
        self.MY_tz = pytz.timezone(self.time_zone)
        return

    async def start_response(self, name):
        response_message = self.greetings.format(name)
        return response_message

    async def rozklad_response(self, new_group):
        new_group = re.sub('[-]', '', new_group)
        response = list()
        if self.xls.find_timetable(new_group, dict()) != dict():
            response = [True, f"Група була змінена на {new_group}"]
        else:
            response = [
                False,
                f"Група не була змінена на {new_group}. "
                f"Мабуть, її немає в таблиці, чи була "
                f"допущена помилка, під час її написання."
            ]
        return response

    async def quick_help_response(self):
        week_num = await self.get_current_week()
        response_message = f"*Week: {week_num}* \n" \
                           f"/today \t\U00002B50\n" \
                           f"/tomorrow \t\U0001F449\n" \
                           f"/week \t\U00002B50\n" \
                           f"/nextweek \t\U0001F449\n" \
                           f"/timetable \t\U0001F6A7\n" \
                           f"/left"
        return response_message

    async def help_response(self, group):
        week_num = await self.get_current_week()

        response_message = f"*{group}*\n*Week: {week_num}*\n" \
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
        return response_message

    async def today_response(self, group, name):
        today = datetime.datetime.now(self.MY_tz)
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
                re.sub(r'[*-: \n]', "", day_temp)
            )

            if get_key_result == -1:
                today_res = day_temp
            else:
                today_res = day_temp
                today_res += "\nСьогодні в тебе *нічого* немає, відпочивай"

        return today_res

    async def tomorrow_response(self, group, name):
        tomorrow = datetime.datetime.now(self.MY_tz)
        tomorrow += datetime.timedelta(days=1)
        week_num = await self.get_current_week(tomorrow)

        weekday = tomorrow.weekday() + 1

        if weekday == 7:
            tomorrow_res = f"Завтра *НЕДІЛЯ*! {name}"

        else:
            day_temp = (self.xls.get_day_timetable(
                group,
                self.timetable,
                weekday,
                week_num
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
                re.sub(r'[*-: \n]', "", day_temp)
            )
            if get_key_result == -1:
                tomorrow_res = day_temp
            else:
                tomorrow_res = day_temp
                tomorrow_res += "\nЗавтра в тебе *нічого* не буде, відпочивай"

        return tomorrow_res

    async def week_response(self, group):
        today = datetime.datetime.now(self.MY_tz)
        week_num = await self.get_current_week(today)

        week_res = self.xls.get_week_timetable(
            group,
            self.timetable,
            week_num
        )
        return week_res

    async def next_week_response(self, group):
        today = datetime.datetime.now(self.MY_tz)
        week_num = 2 if await self.get_current_week(today) == 1 else 1

        next_week_res = self.xls.get_week_timetable(
            group,
            self.timetable,
            week_num
        )
        return next_week_res

    async def full_response(self, group):
        week_res = self.xls.get_week_timetable(group, self.timetable, 1)
        week_res += "\n" * 2
        week_res += self.xls.get_week_timetable(group, self.timetable, 2)
        return week_res

    async def current_lesson_response(self, group, name):  # RUSSISCH LANGUAGE
        now = datetime.datetime.now(self.MY_tz)
        week_num = await self.get_current_week(now)

        weekday = now.weekday() + 1

        if weekday == 7:
            result = f"Сьогодні ж *НЕДІЛЯ*! {name}"
            return result

        result = f"Сьогодні пар більше не буде, бо вже вечір\n" \
                 f"/nextlesson — покаже тобі інформацію про наступну пару"

        now = now.strftime('%X')  # Get time like string HH:MM:SS

        current_point = datetime.datetime.strptime(now, '%H:%M:%S')
        try:
            for i in range(len(self.lesson_end_time)):
                lesson_end_point = datetime.datetime.strptime(
                    self.lesson_end_time[i],
                    '%H:%M'
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
                        week_num,
                        i + 1
                    )
                    result = f"Сейчас идет _{i + 1} пара_:\n"
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

    async def next_lesson_response(self, group, name):  # RUSSISCH LANGUAGE
        now = datetime.datetime.now(self.MY_tz)
        week_num = await self.get_current_week(now)

        result = str()
        weekday = now.weekday() + 1

        now = now.strftime('%X')

        current_point = datetime.datetime.strptime(now, '%H:%M:%S')

        add_days = 0
        try:
            while True:
                for i in range(len(self.lesson_end_time)):
                    lesson_end_point = datetime.datetime.strptime(
                        self.lesson_end_time[i],
                        '%H:%M'
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
                                week_num,
                                i + 1
                            )
                            if next_lesson == '':
                                continue
                            result = f"Следующая будет _{i + 1} пара_:\n"
                            result += next_lesson
                            result += f"\nЧерез *{delta_minutes - 95} мин " \
                                      f"{delta_seconds} сек*"
                            return result
                    else:
                        delta_minutes = tdelta.seconds // 60 - 95
                        delta_hours = delta_minutes // 60 % 24
                        delta_minutes %= 60
                        next_lesson = self.xls.get_current_lesson(
                            group,
                            self.timetable,
                            weekday,
                            week_num,
                            i + 1
                        )
                        if next_lesson == '':
                            continue
                        result = f"Следующая будет _{i + 1} пара_ в " \
                                 f"*{self.day_of_week[str(weekday)]} " \
                                 f"{week_num}*:\n"
                        result += next_lesson
                        result += f"\nЧерез: *{tdelta.days + add_days} дн " \
                                  f"{delta_hours} год {delta_minutes} хв*"
                        return result

                # начинаем проходить каждый день,
                # пока не попадем на пару,
                # а не на окна (пустые пары)

                weekday += 1
                add_days += 1

                # если попало на воскресенье, то мы автоматом
                # переключаемся с него на понедельник

                if weekday == 7:
                    add_days += 1
                    weekday = 1
                    week_num = 1 if week_num == 2 else 2
        except Exception as e:
            print(e)
            result = f"Произошла ошибка, извините..."
        return result

    async def timetable_mes_response(self):
        response_message = self.lessons_schedule
        return response_message

    async def left_response(self, name):  # RUSSISCH LANGUAGE
        now = datetime.datetime.now(self.MY_tz)

        left_result = f"Не могу посчитать время... \n*{name}*, " \
                      f"а сейчас точно пара?"
        now = now.strftime('%X')

        current_point = datetime.datetime.strptime(now, '%H:%M:%S')
        try:
            for i in range(len(self.lesson_end_time)):
                lesson_end_point = datetime.datetime.strptime(
                    self.lesson_end_time[i],
                    '%H:%M'
                )
                tdelta = lesson_end_point - current_point

                if tdelta.days == 0:
                    delta_minutes = tdelta.seconds // 60
                    delta_seconds = tdelta.seconds % 60
                    if delta_minutes > 94:
                        left_result = f"Перемена еще не закончилась.\n" \
                                      f"До начала следующей _({i + 1} пары)" \
                                      f"_ осталось: *{delta_minutes - 95} " \
                                      f"мин {delta_seconds} сек*"
                    else:
                        left_result = f"До конца {i + 1}" \
                                      f" пары осталось: *{delta_minutes} " \
                                      f"мин {delta_seconds} сек*"
                    return left_result
        except Exception as e:
            print(e)
            left_result = f"Не могу посчитать время... \n*{name}*, " \
                          f"а сейчас точно пара?"
        return left_result

    async def find_info_response(self, info_request):
        response_message = self.xls.find_info(info_request)
        return response_message

    async def change_week(self):
        self.week_index = 1 if self.week_index == 0 else 0
        await self.change_week_json()
        response_message = "Week_index successfully has been changed"
        return response_message

    async def update_file(self, url):
        request = requests.get(url)
        req_code = request.status_code
        req_type = request.headers["Content-Type"]
        if req_code == 200 and req_type == "application/vnd.ms-excel":
            with open(
                    f"../{self.folder}/{self.filename}",
                    'wb'
            ) as update_file:
                update_file.write(request.content)
            self.timetable.clear()
            self.xls.update(f"{self.curr_path}../"
                            f"{self.folder}/{self.filename}")
            response_message = f"<b>Увага!</b>\n" \
                               f"Розклад було оновлено.\n" \
                               f"<a href=\"{url}\">" \
                               f"Посилання на новий файл</a>"
            return [True, response_message]
        else:
            response_message = f"URL error (not 200 code or wrong type" \
                               f" must be: \"application/vnd.ms-excel\")"
            return [False, response_message]

    # Additional Functions:

    async def get_current_week(self, time=None):
        if not time:
            time = datetime.datetime.now(self.MY_tz)
        week_num = datetime.date(
            time.year,
            time.month,
            time.day
        ).isocalendar()[1]
        return 1 if week_num % 2 == self.week_index else 2

    async def change_week_json(self):
        with open(self.config_path, encoding='utf-8') as json_file:
            config = json.load(json_file)
        config["week_index"] = self.week_index
        with open(self.config_path, 'w', encoding='utf-8') as json_outfile:
            json.dump(config, json_outfile, indent=4)

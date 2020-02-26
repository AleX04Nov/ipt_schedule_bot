import datetime
import json
import logging
import re
from datetime import timedelta
from logging.handlers import RotatingFileHandler

import pytz
import requests

from xls_handler import XlsHandler


class ScheduleBotManager:
    """
    Class with methods, that are
    not connected with TGAPI.
    Pure Schedule Manager and nothing else
    """
    day_of_week: dict
    timetable: dict
    week_index: int
    lesson_end_time: list
    config_path: str
    curr_path: str
    filename: str
    folder: str
    greetings: str
    lessons_schedule: str
    time_zone: str
    MY_tz: datetime.timezone
    xls: XlsHandler

    def __init__(self, curr_path, config_path):
        with open(curr_path + config_path, encoding='utf-8') as json_file:
            config = json.load(json_file)
        self.day_of_week = config.get("day_of_week")
        self.timetable = dict()
        self.week_index = config.get("week_index")
        self.lesson_end_time = config.get("lesson_end_time")
        self.config_path = config_path
        self.curr_path = curr_path
        self.filename = config.get("filename")
        self.folder = config.get("folder")
        self.greetings = config.get("greetings")
        self.lessons_schedule = config.get("lessons_schedule")
        self.time_zone = config.get("time_zone")
        self.MY_tz = pytz.timezone(self.time_zone)
        xls_path = f"{self.curr_path}../{self.folder}/{self.filename}"
        self.xls = XlsHandler(xls_path, self.day_of_week)

        self.logger = logging.getLogger('scheduleBot_Manager')
        hdlr = logging.handlers.RotatingFileHandler(
            f"{self.curr_path}../{self.folder}/scheduleBot_Manager.log",
            mode='a',
            maxBytes=12 * 1024 * 1024,
            backupCount=2,
        )
        log_format = logging.Formatter(
            '%(asctime)s | %(levelname)-5s | %(message)s',
            datefmt='%d.%m.%Y | %H:%M:%S'
        )
        hdlr.setFormatter(log_format)
        self.logger.addHandler(hdlr)

        return

    async def start_response(self, name):
        """
        Use this method to get `greetings` string
            from current class

        :param name: name of client
        :type name: `str`
        :return: text with greetings
        :rtype: `str`
        """
        response_message = self.greetings.format(name)
        return response_message

    async def rozklad_response(self, new_group):
        """
        Use this method to check if group exists
            and get text response

        :param new_group: group to check
        :type new_group: `str`
        :return: list, where first elem is succession bool
            and the second one is a text with response
        """
        new_group = re.sub('[-]', '', new_group)
        if self.xls.find_timetable(new_group, dict()) != dict():
            response = True, f"Група була змінена на {new_group}"
        else:
            response = (
                False,
                f"Група не була змінена на {new_group}. "
                f"Мабуть, її немає в таблиці, чи була "
                f"допущена помилка, під час її написання."
            )
        return response

    async def quick_help_response(self):
        """
        Use this method to get "quickhelp" text message

        :return: quickhelp text
        :rtype: `str`
        """
        week_num = await self.get_current_week()
        response_message = (
            f"*Week: {week_num}* \n"
            f"/today \t⭐\n"
            f"/tomorrow \t\👉\n"
            f"/week \t\⭐\n"
            f"/nextweek \t👉\n"
            f"/timetable \t🚧\n"
            f"/left"
        )
        return response_message

    async def help_response(self, group):
        """
        Use this method to get "help" text message

        :type group: `str`
        :param group: group of client
        :return: help text
        :rtype: `str`
        """
        week_num = await self.get_current_week()

        response_message = (
            f"*{group}*\n*Week: {week_num}*\n"
            f"Команди:\n\n"
            f"/today — розклад на сьогодні\n"
            f"/tomorrow — розклад на завтра\n"
            f"/week — розклад на поточний тиждень\n"
            f"/nextweek — розклад на наступний тиждень\n"
            f"/timetable — розклад кінця/початку пар\n\n"
            f"/full — повний розклад на два тижні\n"
            f"/left — дізнатися час до кінця пари\n"
            f"/currentLesson — інформація про поточну пару\n"
            f"/nextLesson — інформація про наступну пару\n\n"
            f"/rozklad НАЗВАГРУПИ - змінити показ розкладу"
            f"на іншу групу\n"
            f"/find\_info ЗАПИТ — пошук пар, за запитом "
            f"(кабінет, фамілія викладача, назва предмету,"
            f"тощо). Наприклад: `/find_info Яковлєв`\n\n"
            f"/quickhelp — короткий список команд\n"
            f"/help — показати це повідомлення 😱"
        )
        return response_message

    async def today_response(self, group, name):
        """
        Use this method to get today`s schedule
            for requested group

        :param group: group of client
        :type group: `str`
        :param name: name of client
        :type name: `str`
        :return: text with today`s schedule
        :rtype: `str`
        """
        today = datetime.datetime.now(self.MY_tz)
        week_num = await self.get_current_week(today)

        weekday = today.weekday() + 1

        # if today is Sunday - get response and skip
        # other processing
        if weekday == 7:
            today_res = f"Сьогодні ж *НЕДІЛЯ*! {name}"

        else:
            is_empty, day_temp = self.xls.get_day_timetable(
                group,
                self.timetable,
                weekday,
                week_num
            )

            if is_empty is False:
                today_res = day_temp
            else:
                today_res = day_temp
                today_res += "\nСьогодні в тебе *нічого* немає, відпочивай"

        return today_res

    async def tomorrow_response(self, group, name):
        """
        Use this method to get tomorrow`s schedule
            for requested group

        :param group: group of client
        :type group: `str`
        :param name: name of client
        :type name: `str`
        :return: text with today`s schedule
        :rtype: `str`
        """
        tomorrow = datetime.datetime.now(self.MY_tz) + timedelta(days=1)
        week_num = await self.get_current_week(tomorrow)

        weekday = tomorrow.weekday() + 1

        # if tomorrow will be Sunday - get response and skip
        # other processing
        if weekday == 7:
            tomorrow_res = f"Завтра *НЕДІЛЯ*! {name}"

        else:
            is_empty, day_temp = self.xls.get_day_timetable(
                group,
                self.timetable,
                weekday,
                week_num
            )

            if is_empty is False:
                tomorrow_res = day_temp
            else:
                tomorrow_res = day_temp
                tomorrow_res += "\nЗавтра в тебе *нічого* не буде, відпочивай"

        return tomorrow_res

    async def week_response(self, group):
        """
        Use this method to get current week schedule
            for requested group

        :param group: group of client
        :type group: `str`
        :return: text with current week schedule
        :rtype: `str`
        """
        today = datetime.datetime.now(self.MY_tz)
        week_num = await self.get_current_week(today)

        week_res = self.xls.get_week_timetable(
            group,
            self.timetable,
            week_num
        )
        return week_res

    async def next_week_response(self, group):
        """
        Use this method to get next week schedule
            for requested group

        :param group: group of client
        :type group: `str`
        :return: text with next week schedule
        :rtype: `str`
        """
        today = datetime.datetime.now(self.MY_tz)
        week_num = 2 if await self.get_current_week(today) == 1 else 1

        next_week_res = self.xls.get_week_timetable(
            group,
            self.timetable,
            week_num
        )
        return next_week_res

    async def full_response(self, group):
        """
        Use this method to get full schedule
            for requested group

        :param group: group of client
        :type group: `str`
        :return: text with full schedule
        :rtype: `str`
        """
        week_res = self.xls.get_week_timetable(group, self.timetable, 1)
        week_res += "\n" * 2
        week_res += self.xls.get_week_timetable(group, self.timetable, 2)
        return week_res

    async def current_lesson_response(self, group, name):
        """
        Use this method to get current lesson
            for requested group
            and time till break

        :param group: group of client
        :type group: `str`
        :param name: name of client
        :type name: `str`
        :return: text with info about current lesson
        :rtype: `str`
        """
        now = datetime.datetime.now(self.MY_tz)
        week_num = await self.get_current_week(now)

        weekday = now.weekday() + 1

        # if today is Sunday - get response and skip
        # other processing
        if weekday == 7:
            result = f"Сьогодні ж *НЕДІЛЯ*! {name}"
            return result

        result = (
            f"Сьогодні пар більше не буде, бо вже вечір\n"
            f"/nextlesson — покаже тобі інформацію про наступну пару"
        )

        # Get time like string HH:MM:SS
        now = now.strftime('%X')
        current_point = datetime.datetime.strptime(now, '%H:%M:%S')

        try:
            # get timedelta for every single lesson
            # in a day
            for i in range(len(self.lesson_end_time)):
                lesson_end_point = datetime.datetime.strptime(
                    self.lesson_end_time[i],
                    '%H:%M'
                )
                tdelta = lesson_end_point - current_point

                # if time has passed - there will be -1 days in delta
                # otherwise - 0. We need to process fisrt with
                # 0 one
                if tdelta.days == 0:
                    delta_minutes = tdelta.seconds // 60
                    delta_seconds = tdelta.seconds % 60

                    # length of the lesson is 95 minutes.
                    # if delta higher then 94 - there is still a break
                    if delta_minutes > 94:
                        result = (
                            f"Зачекай, зараз немає пари. Мабуть, йде"
                            f"перерва або все ще ранок, *{name}*, "
                            f"відпочивай\n"
                            f"/nextLesson — покаже тобі інформацію "
                            f"про наступну пару"
                        )
                        return result

                    # else - get current lesson from xml
                    # and show delta as the time till the end of the lesson
                    curr_lesson = self.xls.get_current_lesson(
                        group,
                        self.timetable,
                        weekday,
                        week_num,
                        i + 1
                    )
                    result = f"Наразі йде _{i + 1} пара_:\n"
                    result += curr_lesson
                    result += (
                        f"\nДо кінця цієї пари: *{delta_minutes} хв "
                        f"{delta_seconds} сек*"
                    )
                    if curr_lesson == '':
                        result = (
                            f"Наразі йде _{i + 1} пара_:\n"
                            f"Але у тебе на ній *нічого* немає :)\n"
                            f"------------------------------\n"
                            f"Час до кінця цієї пари: "
                            f"*{delta_minutes} хв {delta_seconds} "
                            f"сек*\n"
                            f"------------------------------\n"
                            f"/nextLesson — покаже тобі інформацію "
                            f"про наступну пару"
                        )
                    return result
        except Exception as e:
            # I give it 1/1000 that there will be an exception
            # but there still some chances, so...
            self.logger.error(e)
            result = f"Йой!\nВиникла помилка..."
        return result

    async def next_lesson_response(self, group, name):
        """
        Use this method to get next lesson
            for requested group
            and time till its start

        :param group: group of client
        :type group: `str`
        :param name: name of client
        :type name: `str`
        :return: text with info about next lesson
        :rtype: `str`
        """
        now = datetime.datetime.now(self.MY_tz)
        week_num = await self.get_current_week(now)

        result = str()
        weekday = now.weekday() + 1

        # Get time like string HH:MM:SS
        now = now.strftime('%X')
        current_point = datetime.datetime.strptime(now, '%H:%M:%S')

        # Do the while loop incrementing days, till there is
        # not an empty lesson in the future.
        # Count time till its beginning
        add_days = 0
        try:
            while True:
                # get timedelta for every single lesson
                # in a day
                for i in range(len(self.lesson_end_time)):
                    lesson_end_point = datetime.datetime.strptime(
                        self.lesson_end_time[i],
                        '%H:%M'
                    )
                    tdelta = lesson_end_point - current_point

                    """
                    This 'if' stays for lessons, that will be
                    in a current day. Thus we have no need in
                    days and hours, but we need to count seconds.
                    Restrictions to lessons: need to chose the first one
                    end of which will come in more than 95 minutes.
                    do not count empty lessons
                    """
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
                            result = f"Наступна буде _{i + 1} пара_:\n"
                            result += next_lesson
                            result += (
                                f"\nЧерез *{delta_minutes - 95} хв "
                                f"{delta_seconds} сек*"
                            )
                            return result
                        """
                        'else' stays for lessons, that will be in some
                        next days (add_days). Also we have no need in seconds
                        but we need to count days and hours additionally
                        Restrictions to lessons: need to chose the first one.
                        do not count empty lessons
                        """
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
                        result = (
                            f"Наступна буде _{i + 1} пара_ в "
                            f"*{self.day_of_week[str(weekday)]} "
                            f"{week_num}*:\n"
                        )
                        result += next_lesson
                        result += (
                            f"\nЧерез: *{tdelta.days + add_days} дн "
                            f"{delta_hours} год {delta_minutes} хв*"
                        )
                        return result

                # check every single day one-by-one,
                # till we get not an empty lesson,
                weekday += 1
                add_days += 1

                # if weekday is Sunday - skip it on Monday
                if weekday == 7:
                    add_days += 1
                    weekday = 1
                    week_num = 1 if week_num == 2 else 2
        except Exception as e:
            # I give it 1/1000 that there will be an exception
            # but there still some chances, so...
            self.logger.error(e)
            result = f"Виникла помилка, вибачте..."
        return result

    async def timetable_mes_response(self):
        """
        Use this method to get lessons timetable

        :return: text with lessons timetable
        :rtype: `str`
        """
        response_message = self.lessons_schedule
        return response_message

    async def left_response(self, name):
        """
        Use this method to get time till
            end of lesson or break

        :param name: name of client
        :type name: `str`
        :return: text with info about time
        :rtype: `str`
        """
        now = datetime.datetime.now(self.MY_tz)

        left_result = (
            f"Не можу порахувати час... \n*{name}*, "
            f"а зараз точно йде пара?"
        )

        # Get time like string HH:MM:SS
        now = now.strftime('%X')
        current_point = datetime.datetime.strptime(now, '%H:%M:%S')
        try:
            # get timedelta for every single lesson
            # in a day
            for i in range(len(self.lesson_end_time)):
                lesson_end_point = datetime.datetime.strptime(
                    self.lesson_end_time[i],
                    '%H:%M'
                )
                tdelta = lesson_end_point - current_point

                # if time has passed - there will be -1 days in delta
                # otherwise - 0. We need to process fisrt with
                # 0 one
                if tdelta.days == 0:
                    delta_minutes = tdelta.seconds // 60
                    delta_seconds = tdelta.seconds % 60
                    # length of the lesson is 95 minutes.
                    # if delta higher then 94 - there is still a break
                    if delta_minutes > 94:
                        left_result = (
                            f"Перерва ще не закінчилася.\n"
                            f"До початку наступної _({i + 1} пари)"
                            f"_ залишилось: *{delta_minutes - 95} "
                            f"хв {delta_seconds} сек*"
                        )
                    else:
                        left_result = (
                            f"До кінця {i + 1} "
                            f"пари залишилось: *{delta_minutes} "
                            f"хв {delta_seconds} сек*"
                        )
                    return left_result
        except Exception as e:
            # I give it 1/1000 that there will be an exception
            # but there still some chances, so...
            self.logger.error(e)
            left_result = (
                f"Не можу порахувати час... \n*{name}*, "
                f"а зараз точно йде пара?"
            )
        return left_result

    async def find_info_response(self, info_request):
        """
        Use this method to get requested info
            from xls table

        :param info_request: info to find
        :return: text with response from xls func
        :rtype: `str`
        """
        response_message = self.xls.find_info(info_request)
        return response_message

    async def change_week(self):
        """
        Use this method to change academic week index in class

        :return: response text
        :rtype: `str`
        """
        self.week_index = 1 if self.week_index == 0 else 0
        await self.change_week_json()
        response_message = "Week_index has been changed successfully"
        return response_message

    async def update_file(self, url):
        """
        Use this method to update xls file.
            Update - means change an old schedule
            file to a new one in data folder

        :param url: Url with new schedule file
        :type url: `str`
        :return: list, where first elem is succession `bool`,
            and the second one is response_message `str`
        """
        if not url:
            response_message = "URL error"
            return False, response_message

        request = requests.get(url)
        req_code = request.status_code
        req_type = request.headers["Content-Type"]

        # Check if request and type are OK
        if not (req_code == 200 and req_type == "application/vnd.ms-excel"):
            response_message = (
                f"URL error (not 200 code or wrong type"
                f" must be: \"application/vnd.ms-excel\")"
            )
            return False, response_message

        with open(
                f"../{self.folder}/{self.filename}",
                'wb'
        ) as update_file:
            update_file.write(request.content)
        self.timetable.clear()
        self.xls.update(
            f"{self.curr_path}../"
            f"{self.folder}/{self.filename}"
        )
        response_message = (
            f"<b>Увага!</b>\n"
            f"Розклад було оновлено.\n"
            f"<a href=\"{url}\">"
            f"Посилання на новий файл</a>"
        )
        return True, response_message

    # Additional Functions:

    async def get_current_week(self, time=None):
        """
        Use this method to get current academic week num

        :param time: timezone. By default it`s set due to tz
            in config file
        :return: int week number (1 or 2)
        """
        if not time:
            time = datetime.datetime.now(self.MY_tz)
        week_num = datetime.date(
            time.year,
            time.month,
            time.day
        ).isocalendar()[1]
        return 1 if week_num % 2 == self.week_index else 2

    async def change_week_json(self):
        """
        Use this method to save new class academic week index
            into current json config file

        :return: None
        """
        with open(self.config_path, encoding='utf-8') as json_file:
            config = json.load(json_file)
        config["week_index"] = self.week_index
        with open(self.config_path, 'w', encoding='utf-8') as json_outfile:
            json.dump(config, json_outfile, indent=4)

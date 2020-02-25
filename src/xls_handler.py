import re
import xlrd


def get_key(d, value):
    for k, v in d.items():
        if v == value:
            return k
    return -1


class XlsHandler:
    day_of_week: dict
    merged_dict: dict
    rb: xlrd.book
    sheet: xlrd.sheet

    def __init__(self, path, day_of_week):
        self.day_of_week = day_of_week
        self.merged_dict = dict()
        self.rb = None
        self.sheet = None
        self.update(path)

    def update(self, path):
        self.rb = xlrd.open_workbook(path, formatting_info=True)
        self.sheet = self.rb.sheet_by_index(0)
        self.merge_cells()

    ######################################################
    # !!!         XLS PARSING BELOW          !!! #

    def merge_cells(self,):
        """
        Use this method to store merged cells in xls
            document

        :return: None
        """
        merged = self.sheet.merged_cells
        self.merged_dict = dict()
        for i in range(len(merged)):
            a = merged[i][0]
            b = merged[i][1]
            for rowx in range(a, b):
                c = merged[i][2]
                d = merged[i][3]
                for colx in range(c, d):
                    self.merged_dict[
                        (rowx, colx)
                    ] = self.sheet.cell_value(a, c)

    def find_timetable(self, group_name, timetable):
        """
        Use this method to update timetable dict with
            requested group

        :param group_name: group to find in xls
        :type group_name: `str`
        :param timetable: timetable object outside of this class
        :type timetable: `dict`
        :return: updated timetable object
        :rtype: `dict`
        """
        if group_name == '':
            return timetable
        res = timetable
        sheet = self.sheet
        merged_dict = self.merged_dict
        for main_col in range(sheet.ncols):
            for main_row in range(sheet.nrows):
                name_quest = str(sheet.cell_value(main_row, main_col)).lower()
                name_quest = re.sub('[-]', '', name_quest)
                if name_quest == group_name:
                    res[group_name] = dict()
                    for i in range(2):
                        res[group_name][f"week: {i + 1}"] = dict()
                        j = 0
                        les = 0
                        for row in range(4, sheet.nrows):
                            if (row - 4) % 15 == 0:
                                j += 1
                                les = 0
                                if j == 7:
                                    break
                                group_dict = res[group_name]
                                week_dict = group_dict[f"week: {i + 1}"]
                                week_dict[f"day: {j}"] = dict()
                            if row % 3 == (2 + i) % 3:
                                les += 1
                                value = sheet.cell_value(row, main_col)
                                if value == "":
                                    value = merged_dict.get(
                                        (row, main_col),
                                        ""
                                    )
                                if len(value) <= 1:
                                    value = ""
                                value = re.sub('[\n]', ' ', value)
                                group_dict = res[group_name]
                                week_dict = group_dict[f"week: {i + 1}"]
                                day_dict = week_dict[f"day: {j}"]
                                day_dict[f"{les} lesson: "] = value
                    return res
        return res

    def get_current_lesson(
        self,
        group,
        table_dict,
        day_index,
        week_index,
        lesson_index
    ):
        """
        Use this method to get an exact lesson

        :param group:
        :param table_dict: dict with parsed groups and their schedule
        :param day_index: number of day in a week
        :param week_index: academic week index
        :param lesson_index: number of lesson in a day
        :return: value of lesson cell in xls
        """
        group_dict = table_dict[group]
        week_dict = group_dict[f"week: {week_index}"]
        day_dict = week_dict[f"day: {day_index}"]
        value = day_dict[f"{lesson_index} lesson: "]
        return value

    def get_day_timetable(
            self,
            group,
            table_dict,
            day_index,
            week_index,
            format=True,
            mode=False
    ):
        """
        Use this method to get string with lessons
            for an exact group and exact day in markdown style

            Example:
            *day {academic num of week}*   This part can be in
            *-------------------------*    reverse style. See `mode`
            *1)* Lesson 1
            *2)* Lesson 2
            *3)* _----_ (empty Lesson 3)
            *4)* Lesson 4
            *5)* _----_ (empty Lesson 5)

        if `format` is True - empty lessons in the end of the day - deleted
            Example:
            *day {academic num of week}*
            *-------------------------*
            *1)* Lesson 1
            *2)* Lesson 2
            *3)* _----_ (empty Lesson 3)
            *4)* Lesson 4

        :param group:
        :param table_dict: dict with parsed groups and their schedule
        :param day_index: number of day in a week
        :param week_index: academic week index
        :param format: `bool` default True
        :param mode: `bool` change header order. Default False
        :return: string with parsed markdown-like style data
        """
        is_empty = False

        if mode is False:
            res = f"*{self.day_of_week[str(day_index)]} {week_index}*\n" \
                  f"*-------------------------*\n"
        else:
            res = f"*-------------------------*\n" \
                  f"*{self.day_of_week[str(day_index)]}:*\n"
        group_dict = table_dict[group]
        week_dict = group_dict[f"week: {week_index}"]
        day_dict = week_dict[f"day: {day_index}"]

        for lesson in range(1, 6):
            value = day_dict[f"{lesson} lesson: "]
            if value == "":
                value = "_----_"
            res += f"*{lesson})* {value}\n"

        res = res[:-1]

        if format is True:
            day_temp = res

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

            res = day_temp

            if get_key_result != -1:
                is_empty = True

        return [is_empty, res]

    def get_week_timetable(self, group, table_dict, week_index):
        """
        Use this method to get markdown-likes styled string
            with parsed schedule for a group.
            Days with no lessons - not count

        :param group:
        :param table_dict: dict with parsed groups and their schedule
        :param week_index: academic week index
        :return: string with parsed markdown-like style data
        """
        res = f"*Тиждень: {week_index}*\n"
        for day_index in range(1, 7):

            day_temp = self.get_day_timetable(
                group,
                table_dict,
                day_index,
                week_index,
                mode=True
            )

            if day_temp[0] is False:
                res += day_temp[1] + '\n'
            else:
                res += ''
        res += "*-------------------------*"
        return res

    def find_info(self, request):
        """
        Use this method to get all cells that contain request in it
            Thus xls file is very complex - this func is look like complex too
            After retrieving cells - we parse them like full timetable func
            (2 weeks one-by-one)

        :param request: request to find in xls file
        :return: markdown styled string
        """
        sheet = self.sheet
        merged_dict = self.merged_dict
        res = dict()
        res[request] = dict()
        value = str()
        for i in range(2):
            res[request][f"week: {i + 1}"] = dict()
            for j in range(1, 7):
                request_dict = res[request]
                week_dict = request_dict[f"week: {i + 1}"]
                week_dict[f"day: {j}"] = dict()
                for les in range(1, 6):
                    day_dict = week_dict[f"day: {j}"]
                    day_dict[f"{les} lesson: "] = ""
        bool_found = False
        for main_col in range(sheet.ncols):
            for main_row in range(sheet.nrows):
                cell_value = sheet.cell_value(main_row, main_col)
                request_in_cell = (
                    str(cell_value).lower()
                ).find(request.lower())

                if request_in_cell != -1:
                    bool_found = True
                    week = 1 if main_row % 3 == 2 else 2
                    day = (
                        (main_row - ((main_row - 4) % 15) + 1 - 6) // 15
                    ) + 2

                    if str(sheet.cell_value(main_row, 1)) != "":
                        lesson = int(sheet.cell_value(main_row, 1))
                    else:
                        lesson = int(sheet.cell_value(main_row - 1, 1))

                    groups = str(sheet.cell_value(3, main_col))
                    iter = 1

                    while True:
                        cell_value_iter = sheet.cell_value(
                            main_row,
                            main_col + iter
                        )
                        if str(cell_value_iter) != "":
                            break

                        merged_cell = merged_dict.get(
                            (main_row, main_col + iter),
                            ""
                        )

                        if merged_cell != "" and merged_cell == cell_value:
                            groups += ", "
                            cell_value_2 = sheet.cell_value(2, main_col + iter)
                            cell_value_3 = sheet.cell_value(3, main_col + iter)
                            if str(cell_value_2) == "":
                                groups += str(cell_value_3)
                            else:
                                groups += str(cell_value_2)
                                groups += ", "
                                groups += str(cell_value_3)

                        iter += 1

                    request_dict = res[request]
                    week_dict = request_dict[f"week: {week}"]
                    day_dict = week_dict[f"day: {day}"]
                    if day_dict[f"{lesson} lesson: "] == "":
                        day_dict[f"{lesson} lesson: "] = f"{str(cell_value)}" \
                                                       f" *{groups}*"
                    else:
                        day_dict[f"{lesson} lesson: "] += f"\n||\n" \
                                                        f"{str(cell_value)} " \
                                                        f"*{groups}*"

                    if week == 1:
                        value = sheet.cell_value(main_row + 1, main_col)
                        if str(value) == "":
                            value = merged_dict.get(
                                (main_row + 1, main_col),
                                ""
                            )

                    if week == 1 and str(value) == str(cell_value):
                        week_dict = request_dict["week: 2"]
                        day_dict = week_dict[f"day: {day}"]

                        if day_dict[f"{lesson} lesson: "] == "":
                            day_dict[f"{lesson} lesson: "] = f"{str(value)} " \
                                                            f"*{groups}*"
                        else:
                            day_dict[f"{lesson} lesson: "] += f"\n||\n" \
                                                            f"{str(value)} " \
                                                            f"*{groups}*"

        if bool_found is False:
            return "На жаль дана інформація не була знайдена у таблиці. :с"

        week_res = self.get_week_timetable(request, res, 1)
        week_res += "\n" * 2 + self.get_week_timetable(request, res, 2)
        return week_res
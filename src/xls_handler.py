import re
import xlrd


def get_key(d, value):
    for k, v in d.items():
        if v == value:
            return k
    return -1


class XlsHandler:
    def __init__(self, path, day_of_week):
        self.day_of_week = day_of_week
        self.rb          = None
        self.sheet       = None
        self.merged_dict = None
        self.update(path)

    def update(self, path):
        self.rb          = xlrd.open_workbook(path, formatting_info=True)
        self.sheet       = self.rb.sheet_by_index(0)
        self.merge_cells()

    ######################################################
    # !!!         XLS ROZKLAD PARSING BELOW          !!! #

    def merge_cells(self,):
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

    def print_timetable(self, group, table_dict):
        print("<======= GROUP ", group, " GROUP =======>")
        group_table = table_dict[group]
        for i in range(1, 3):
            print("Week: ", i)
            week = group_table[f"week: {i}"]
            for j in range(1, 7):
                print("---------------------\nDay: ", j)
                day = week[f"day: {j}"]
                for les in range(1, 6):
                    value = day[f"{les} lesson: "]
                    print(les, " Lesson: ", value)
            print("=====================================")

    def get_day_timetable(self, group, table_dict, day_index, week_index):
        res = f"*{self.day_of_week[str(day_index)]} {week_index}*\n" \
              f"*-------------------------*\n"
        group_table = table_dict[group]
        week = group_table[f"week: {week_index}"]
        day = week[f"day: {day_index}"]

        for les in range(1, 6):
            value = day[f"{les} lesson: "]
            if value == "":
                value = "_----_"
            res += f"*{les})* {value}\n"

        return res

    def get_current_lesson(
        self,
        group,
        table_dict,
        day_index,
        week_index,
        lesson_index
    ):
        group_dict = table_dict[group]
        week_dict = group_dict[f"week: {week_index}"]
        day_dict = week_dict[f"day: {day_index}"]
        value = day_dict[f"{lesson_index} lesson: "]
        return value

    def get_day_for_week_timetable(
        self,
        group,
        table_dict,
        day_index,
        week_index
    ):
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

        return res

    def find_info(self, request):
        sheet = self.sheet
        merged_dict = self.merged_dict
        res = dict()
        res[request] = dict()
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

    def get_week_timetable(self, group, table_dict, week_index):
        res = f"*Тиждень: {week_index}*\n"
        for day_index in range(1, 7):

            day_temp = self.get_day_for_week_timetable(
                group,
                table_dict,
                day_index,
                week_index
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
                res += day_temp + '\n'
            else:
                res += ''
        res += "*-------------------------*"
        return res
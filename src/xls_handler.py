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
        self.rb          = xlrd.open_workbook(path, formatting_info = True)
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
        res = timetable
        sheet = self.sheet
        merged_dict = self.merged_dict
        for main_col in range(sheet.ncols):
            for main_row in range(sheet.nrows):
                name_quest = str(sheet.cell_value(main_row, main_col)).lower()
                name_quest = re.sub('[-]', '', name_quest)
                if name_quest == group_name and name_quest != '':
                    res[name_quest] = dict()
                    for i in range(2):
                        res[name_quest]["week: {}".format(i + 1)] = dict()
                        j = 0
                        for row in range(4, sheet.nrows):
                            if (row - 4) % 15 == 0:
                                j += 1
                                les = 0
                                if j == 7:
                                    break
                                res[
                                    name_quest
                                ][
                                    "week: {}".format(i + 1)
                                ][
                                    "day: {}".format(j)
                                ] = dict()
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
                                res[
                                    name_quest
                                ][
                                    "week: {}".format(i + 1)
                                ][
                                    "day: {}".format(j)
                                ][
                                    "{} lesson: ".format(les)
                                ] = value
                    return res
        return res

    def print_timetable(self, group, table_dict):
        print("<======= GROUP ", group, " GROUP =======>")
        group_table = table_dict[group]
        for i in range(1, 3):
            print("Week: ", i)
            week = group_table["week: {}".format(i)]
            for j in range(1, 7):
                print("---------------------\nDay: ", j)
                day = week["day: {}".format(j)]
                for les in range(1, 6):
                    value = day["{} lesson: ".format(les)]
                    print(les, " Lesson: ", value)
            print("=====================================")

    def get_day_timetable(self, group, table_dict, day_index, week_index):
        res = "*{}".format(
            self.day_of_week[str(day_index)]
        ) + " {}*\n*-------------------------*\n".format(week_index)
        group_table = table_dict[group]
        week = group_table["week: {}".format(week_index)]
        day = week["day: {}".format(day_index)]

        for les in range(1, 6):
            value = day["{} lesson: ".format(les)]
            if value == "":
                value = "_----_"
            res += "*{})* ".format(les) + "{}\n".format(value)

        return res

    def get_current_lesson(
        self,
        group,
        table_dict,
        day_index,
        week_index,
        less_index
    ):
        value = table_dict[
            group
        ][
            "week: {}".format(week_index)
        ][
            "day: {}".format(day_index)
        ][
            "{} lesson: ".format(less_index)
        ]
        return value

    def get_day_for_week_timetable(
        self,
        group,
        table_dict,
        day_index,
        week_index
    ):
        res = "*-------------------------*\n*{}:*\n".format(
            self.day_of_week[str(day_index)]
        )
        group_table = table_dict[group]
        week = group_table["week: {}".format(week_index)]
        day = week["day: {}".format(day_index)]

        for les in range(1, 6):
            value = day["{} lesson: ".format(les)]
            if value == "":
                value = "_----_"
            res += "*{})* ".format(les) + "{}\n".format(value)

        return res

    def find_info(self, request):
        sheet = self.sheet
        merged_dict = self.merged_dict
        res = dict()
        res[request] = dict()
        for i in range(2):
            res[request]["week: {}".format(i + 1)] = dict()
            for j in range(1, 7):
                res[
                    request
                ][
                    "week: {}".format(i + 1)
                ][
                    "day: {}".format(j)
                ] = dict()
                for les in range(1, 6):
                    res[
                        request
                    ][
                        "week: {}".format(i + 1)
                    ][
                        "day: {}".format(j)
                    ][
                        "{} lesson: ".format(les)
                    ] = ""
        bool_found = False
        for main_col in range(sheet.ncols):
            for main_row in range(sheet.nrows):
                if (
                    str(sheet.cell_value(
                        main_row,
                        main_col
                    )).lower()
                ).find(request.lower()) != -1:
                    bool_found = True
                    week = 1 if main_row % 3 == 2 else 2
                    day = (
                        (main_row - ((main_row - 4) % 15) + 1 - 6) // 15
                    ) + 2

                    lesson = int(sheet.cell_value(main_row, 1)) if str(
                        sheet.cell_value(main_row, 1)
                    ) != "" else int(sheet.cell_value(main_row - 1, 1))

                    groups = str(sheet.cell_value(3, main_col))
                    iter = 1
                    while True:
                        if str(
                            sheet.cell_value(main_row, main_col + iter)
                        ) != "":
                            break
                        if str(
                            merged_dict.get((main_row, main_col + iter), "")
                        ) != "" and str(
                            merged_dict.get((main_row, main_col + iter), "")
                        ) == sheet.cell_value(main_row, main_col):
                            groups += ", "
                            groups += str(
                                sheet.cell_value(3, main_col + iter)
                            ) if str(
                                sheet.cell_value(2, main_col + iter)
                            ) == "" else str(
                                sheet.cell_value(2, main_col + iter)
                            ) + ", " + str(
                                sheet.cell_value(3, main_col + iter)
                            )
                        iter += 1

                    if res[
                        request
                    ][
                        "week: {}".format(week)
                    ][
                        "day: {}".format(day)
                    ][
                        "{} lesson: ".format(lesson)
                    ] == "":
                        res[
                            request
                        ][
                            "week: {}".format(week)
                        ][
                            "day: {}".format(day)
                        ][
                            "{} lesson: ".format(lesson)
                        ] = str(
                            sheet.cell_value(main_row, main_col)
                        ) + " *" + groups + "*"
                    else:
                        res[
                            request
                        ][
                            "week: {}".format(week)
                        ][
                            "day: {}".format(day)
                        ][
                            "{} lesson: ".format(lesson)
                        ] += "\n||\n" + str(
                            sheet.cell_value(main_row, main_col)
                        ) + " *" + str(sheet.cell_value(3, main_col)) + "*"

                    if week == 1:
                        value = sheet.cell_value(main_row + 1, main_col)
                        if str(value) == "":
                            value = merged_dict.get(
                                (main_row + 1, main_col),
                                ""
                            )

                    if week == 1 and str(value) == str(
                        sheet.cell_value(main_row, main_col)
                    ):
                        if res[
                            request
                        ][
                            "week: 2"
                        ][
                            "day: {}".format(day)
                        ][
                            "{} lesson: ".format(lesson)
                        ] == "":
                            res[
                                request
                            ][
                                "week: 2"
                            ][
                                "day: {}".format(day)
                            ][
                                "{} lesson: ".format(lesson)
                            ] = str(value) + " *" + groups + "*"
                        else:
                            res[
                                request
                            ][
                                "week: 2"
                            ][
                                "day: {}".format(day)
                            ][
                                "{} lesson: ".format(lesson)
                            ] += "\n||\n" + str(value) + " *" + groups + "*"

        if bool_found is False:
            return "На жаль дана інформація не була знайдена у таблиці. :с"

        week_res = self.get_week_timetable(request, res, 1)
        week_res += "\n" * 2 + self.get_week_timetable(request, res, 2)
        return week_res

    def get_week_timetable(self, group, table_dict, week_index):
        res = "*Тиждень: {}*\n".format(week_index)
        for day_index in range(1, 7):

            day_temp = self.get_day_for_week_timetable(
                group,
                table_dict,
                day_index,
                week_index
            )

            day_temp = day_temp[:-1]

            ### DELETING EMPTY LESSONS ###

            for del_str in range(5, 0, -1):
                if day_temp.rfind("_----_") == len(day_temp) - 6:
                    day_temp = day_temp[:(
                        day_temp.rfind("*{})*".format(del_str))
                    ) - 1]

            ### DELETING EMPTY DAYS ###

            if get_key(
                self.day_of_week,
                re.sub(r'[*-: \n]', "", day_temp)
            ) == -1:
                res += day_temp + '\n'
            else:
                res += ''
        res += "*-------------------------*"
        return res

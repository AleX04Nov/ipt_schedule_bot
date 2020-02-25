import sys
import pathlib
import aiogram

from scheduleBot_Manager_TGAPI import ScheduleBotTGAPI \
    as ScheduleBotManager

curr_path = str(pathlib.Path(__file__).parent.absolute()) + "/"

bot_manager = ScheduleBotManager(
    curr_path,
    "../config/config.json",
    "../config/config_secret.json"
)

####################


@bot_manager.dp.message_handler(commands=["start"])
async def start(message: aiogram.types.message):
    await bot_manager.start(message)


@bot_manager.dp.message_handler(commands=["rozklad"])
async def rozklad(message: aiogram.types.message):
    await bot_manager.rozklad(message)


@bot_manager.dp.message_handler(commands=["quickhelp"])
async def quick_help(message: aiogram.types.message):
    await bot_manager.quick_help(message)


@bot_manager.dp.message_handler(commands=["help"])
async def help_com(message: aiogram.types.message):
    await bot_manager.help(message)


@bot_manager.dp.message_handler(commands=["today"])
async def today(message: aiogram.types.message):
    await bot_manager.today(message)


@bot_manager.dp.message_handler(commands=["tomorrow"])
async def tomorrow(message: aiogram.types.message):
    await bot_manager.tomorrow(message)


@bot_manager.dp.message_handler(commands=["week"])
async def week(message: aiogram.types.message):
    await bot_manager.week(message)


@bot_manager.dp.message_handler(commands=["nextweek"])
async def next_week(message: aiogram.types.message):
    await bot_manager.next_week(message)


@bot_manager.dp.message_handler(commands=["full"])
async def full(message: aiogram.types.message):
    await bot_manager.full(message)


@bot_manager.dp.message_handler(commands=["timetable"])
async def timetable(message: aiogram.types.message):
    await bot_manager.timetable_mes(message)


@bot_manager.dp.message_handler(commands=["left"])
async def left(message: aiogram.types.message):
    await bot_manager.left(message)


@bot_manager.dp.message_handler(commands=["currentlesson"])
async def currentlesson(message: aiogram.types.message):
    await bot_manager.current_lesson(message)


@bot_manager.dp.message_handler(commands=["nextlesson"])
async def nextlesson(message: aiogram.types.message):
    await bot_manager.next_lesson(message)


@bot_manager.dp.message_handler(commands=["update_file"])
async def update_file(message: aiogram.types.message):
    await bot_manager.update_file(message)


@bot_manager.dp.message_handler(commands=["change_week"])
async def change_week(message: aiogram.types.message):
    await bot_manager.change_week(message)


@bot_manager.dp.message_handler(commands=["find_info"])
async def find_info(message: aiogram.types.message):
    await bot_manager.find_info(message)


def main():
    print('Перезапуск🥰')
    try:
        aiogram.executor.start_polling(bot_manager.dp, skip_updates=True)
    except Exception as e:
        print(e)
        bot_manager.close()
    except KeyboardInterrupt:
        print("Closing instance")
        bot_manager.close()
        sys.exit(0)


if __name__ == '__main__':
    main()

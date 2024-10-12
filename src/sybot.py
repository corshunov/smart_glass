import asyncio
from os import getenv
from pathlib import Path
import sys

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile

import sycfg as c
import syfiles

syfiles.reconfigure_stdout()

if len(sys.argv) == 2 and sys.argv[1] == "--dev":
    CHAT_ID = getenv("CHAT_ID_DEV")
else:
    CHAT_ID = getenv("CHAT_ID")

TOKEN = getenv("BOT_TOKEN")
ADMIN_ID = getenv("ADMIN_ID")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)

bot_cmds = [
    ("/start", "Start bot."),
    ("/help", "Show help message."),

    ("/temperature", "Show CPU temperature at the moment."),

    ("/state", "Show system state: ON, OFF."),
    ("/on", "Turn on the system."),
    ("/off", "Turn off the system."),

    ("/mode", "Show mode: MANUAL, AUTO."),
    ("/manual", "Set mode to MANUAL."),
    ("/auto", "Set mode to AUTO."),

    ("/glstate", "Show glass state: TRANSPARENT, OPAQUE."),
    ("/glon", "Set glass state to transparent (relevant only in MANUAL mode)."),
    ("/gloff", "Set glass state to opaque (relevant only in MANUAL mode)."),

    ("/frame", "Show frame at the moment plus its levels."),

    ("/ref", "Show reference frame currently used."),
    ("/updateref", "Set reference frame to frame taken at the moment and show it."),

    ("/thr", "Show level thresholds."),
    ("/updatethr", "Set level thresholds."),
]

async def is_from_group(msg, notify=False):
    if msg.chat.id == CHAT_ID:
        return True

    if notify:
        await msg.answer("Bot can be used in its dedicated group only.")

    return False

async def is_from_admin(msg, notify=False):
    if msg.from_user.id == ADMIN_ID:
        return True

    if notify:
        await msg.send_message(CHAT_ID, "Command can be used by admin only.")

    return False


async def system_is_on(notify=False):
    state = utils.get_state()
    if state == "ON":
        return True

    if notify:
        await bot.send_message(CHAT_ID, "System if OFF. Use command /on to turn it on first.")

    return False

async def mode_is_manual(notify=False):
    mode = utils.get_mode()
    if mode == "MANUAL":
        return True

    if notify:
        await bot.send_message(CHAT_ID, "Mode is AUTO. Use command /manual to enable manual mode first.")

    return False

async def send_frame(fpath, caption):
    dt_str = utils.get_nice_dt_str_from_fpath(fpath)
    caption = f"{caption}\n({dt_str})"

    file = FSInputFile(fpath)
    await bot.send_photo(CHAT_ID, file, caption=caption)

    fpath_new = fpath.parent / f"done.{fpath.name}"
    utils.move_file(fpath, fpath_new)

async def send_on_frames():
    await asyncio.sleep(config.BOT_DELAY_ON_START)

    while True:
        files = sorted(utils.frames_dpath.glob(f"frame_request*{config.PICTURE_EXT}"))
        caption = "Current frame requested"
        for fpath in files:
            await send_frame(fpath, caption)
            await asyncio.sleep(3)


        files = sorted(utils.frames_dpath.glob(f"frame_reference_update*{config.PICTURE_EXT}"))
        caption = "Reference frame updated"
        for fpath in files:
            await send_frame(fpath, caption)
            await asyncio.sleep(3)

        files = sorted(utils.frames_dpath.glob(f"frame_glass_transparent*{config.PICTURE_EXT}"))
        caption = "Glass changed to TRANSPARENT"
        for fpath in files:
            await send_frame(fpath, caption)
            await asyncio.sleep(3)

        files = sorted(utils.frames_dpath.glob(f"frame_glass_opaque*{config.PICTURE_EXT}"))
        caption = "Glass changed to OPAQUE"
        for fpath in files:
            await send_frame(fpath, caption)
            await asyncio.sleep(3)

        await asyncio.sleep(3)

async def send_on_update_thresholds():
    await asyncio.sleep(config.BOT_DELAY_ON_START)

    while True:
        if utils.update_thresholds_fpath.is_file():
            utils.remove_file(update_thresholds_fpath)

            thr_l, thr_r = utils.get_thresholds()
            await bot.send_message(CHAT_ID, f"Thresholds: {thr_l}, {thr_r}.")

        await asyncio.sleep(3)
        
@dp.message(Command('start'))
async def cmd__start(message: Message):
    if not is_from_group(message, notify=True):
        return

    await message.answer("Welcome! Use /help to see details about bot.")

@dp.message(Command('help'))
async def cmd__help(message: Message):
    if not is_from_group(message, notify=True):
        return

    bot_cmds_text = "\n".join([f"{cmd}\n{description}\n" for (cmd, description) in bot_cmds])
    await message.answer(f"I am Smart Glass Bot.\n\nAvailable commands:\n{bot_cmds_text}")

@dp.message(Command('temperature'))
async def cmd__temperature(message: Message):
    if not is_from_group(message):
        return

    t_cpu = utils.get_temperature()
    await message.answer(f"CPU temperature: {t_cpu:.1f} C.")

@dp.message(Command('state'))
async def cmd__state(message: Message):
    if not is_from_group(message):
        return

    state = utils.get_state()
    await message.answer(f"System is {state}.")

@dp.message(Command('on'))
async def cmd__on(message: Message):
    if not is_from_group(message):
        return

    if not is_from_admin(message, notify=True):
        return

    state = utils.get_state()
    if state == "ON":
        await message.answer("System is already {state}.")
        return

    utils.set_state("ON")
    await message.answer("System is ON now.")

@dp.message(Command('off'))
async def cmd__off(message: Message):
    if not is_from_group(message):
        return

    if not is_from_admin(message, notify=True):
        return

    state = utils.get_state()
    if state == "OFF":
        await message.answer("System is already {state}.")
        return

    utils.set_state("OFF")
    await message.answer("System is OFF now.")

@dp.message(Command('mode'))
async def cmd__mode(message: Message):
    if not is_from_group(message):
        return

    mode = utils.get_mode()
    await message.answer(f"Mode is {mode}.")

@dp.message(Command('manual'))
async def cmd__manual(message: Message):
    if not is_from_group(message):
        return

    if not is_from_admin(message, notify=True):
        return

    mode = utils.get_mode()
    if mode == "MANUAL":
        await message.answer("Mode is already {mode}.")
        return

    utils.set_mode("MANUAL")
    await message.answer("MANUAL mode enabled.")

@dp.message(Command('auto'))
async def cmd__auto(message: Message):
    if not is_from_group(message):
        return

    if not is_from_admin(message, notify=True):
        return

    mode = utils.get_mode()
    if mode == "AUTO":
        await message.answer("Mode is already {mode}.")
        return

    utils.set_mode("AUTO")
    await message.answer("AUTO mode enabled.")

@dp.message(Command('glstate'))
async def cmd__glstate(message: Message):
    if not is_from_group(message):
        return

    if not system_is_on(notify=True):
        return

    glstate = utils.get_glass_state()
    await message.answer(f"Glass state is {glstate}.")

@dp.message(Command('glon'))
async def cmd__glon(message: Message):
    if not is_from_group(message):
        return

    if not system_is_on(notify=True):
        return

    if not mode_is_manual(notify=True):
        return

    glstate = utils.get_glass_state()
    if glstate == "TRANSPARENT":
        await message.answer(f"Glass state is already {glstate}.")
        return

    utils.set_glass_state("TRANSPARENT")

@dp.message(Command('gloff'))
async def cmd__gloff(message: Message):
    if not is_from_group(message):
        return

    if not system_is_on(notify=True):
        return

    if not mode_is_manual(notify=True):
        return

    glstate = utils.get_glass_state()
    if glstate == "OPAQUE":
        await message.answer(f"Glass state is already {glstate}.")
        return

    utils.set_glass_state("OPAQUE")

@dp.message(Command('frame'))
async def cmd__frame(message: Message):
    if not is_from_group(message):
        return

    if not system_is_on(notify=True):
        return

    utils.request_frame()

@dp.message(Command('ref'))
async def cmd__frame(message: Message):
    if not is_from_group(message):
        return

    files = sorted(utils.reference_frames_dpath.glob(f"frame_reference*{config.PICTURE_EXT}"))
    if len(files) == 0:
        await message.answer("No reference frames found")
        return

    fpath = files[-1]
    caption = "Reference frame requested"
    await send_frame(fpath, caption)

@dp.message(Command('updateref'))
async def cmd__frame(message: Message):
    if not is_from_group(message):
        return

    if not system_is_on(notify=True):
        return

    utils.request_update_reference_frame()

@dp.message(Command('thr'))
async def cmd__frame(message: Message):
    if not is_from_group(message):
        return

    thr_l, thr_r = utils.get_thresholds()
    await message.answer(f"Thresholds: {thr_l}, {thr_r}.")

@dp.message(Command('updatethr'))
async def cmd__frame(message: Message):
    if not is_from_group(message):
        return

    if not system_is_on(notify=True):
        return

    utils.request_update_thresholds()

#@dp.message()
#async def cmd__any(message: Message):
    #await message.answer("Answered")

async def main():
    await bot.send_message(CHAT_ID, "Smart Glass Bot started.")

    asyncio.create_task(send_on_frames())
    asyncio.create_task(send_on_update_thresholds())

    await dp.start_polling(bot)
    

if __name__ == '__main__':
    utils.prepare_folders(clean=False)
    asyncio.run(main())

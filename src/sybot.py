import asyncio
from datetime import timedelta
from os import getenv
from pathlib import Path
import sys

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile

import sycam
import sycfg as c
import sydt
import syfiles
import syglstate
import sylight
import symode
import systate
import sytemp
import sythr

syfiles.reconfigure_stdout()

if len(sys.argv) == 2 and sys.argv[1] == "--dev":
    CHAT_ID = getenv("CHAT_ID_DEV")
else:
    CHAT_ID = getenv("CHAT_ID")

TOKEN = getenv("BOT_TOKEN")
ADMIN_ID = getenv("ADMIN_ID")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)

bot_public_cmds = [
    ("/start", "start bot"),
    ("/help", "show commands"),
    ("/state", "show system state"),
    ("/frame", "show current frame"),
    ("/ref", "show current reference frame"),
]

bot_admin_cmds = [
    ("/on", "turn ON the system"),
    ("/off", "turn OFF the system"),
    ("/manual", "set mode to MANUAL"),
    ("/auto", "set mode to AUTO"),
    ("/glon", "turn ON the glass (MANUAL mode only)"),
    ("/gloff", "turn OFF the glass (MANUAL mode only)"),
    ("/updateref", "set reference frame to current frame and show it"),
    ("/updatethr", "set level thresholds"),
]

async def is_from_group(msg, notify=False):
    if str(msg.chat.id) == CHAT_ID:
        return True

    if notify:
        await msg.reply(f"{c.EMODJI_WARNING} Bot can be used in its dedicated group only.")

    return False

async def is_from_admin(msg, notify=False):
    if str(msg.from_user.id) == ADMIN_ID:
        return True

    if notify:
        await msg.reply(f"{c.EMODJI_WARNING} Command can be used by admin only.")

    return False


async def system_is_on(msg, notify=False):
    state = systate.get()
    if state == systate.ON:
        return True

    if notify:
        await msg.reply(f"{c.EMODJI_WARNING} System is {systate.OFF}.\nUse command /on to turn it {systate.ON} first.")

    return False

async def mode_is_manual(msg, notify=False):
    mode = symode.get()
    if mode == symode.MANUAL:
        return True

    if notify:
        await msg.reply(f"{c.EMODJI_WARNING} Mode is {symode.AUTO}.\nUse command /manual to enable {symode.MANUAL} mode first.")

    return False

async def send_frame(fpath, caption, rename=True):
    file = FSInputFile(fpath)
    await bot.send_photo(CHAT_ID, file, caption=caption)

    if rename:
        fname_new = fpath.name.replace('-', '')
        fpath_new = fpath.parent / fname_new
        syfiles.move_file(fpath, fpath_new)

async def send_ping():
    await asyncio.sleep(c.BOT_DELAY_ON_START)

    text = "Ping"
    delta = timedelta(minutes=1)

    await bot.send_message(ADMIN_ID, text)
    next_dt = sydt.now() + delta

    while True:
        if sydt.now() > next_dt:
            await bot.send_message(ADMIN_ID, text)
            next_dt = sydt.now() + delta

        await asyncio.sleep(5)

async def send_on_states():
    await asyncio.sleep(c.BOT_DELAY_ON_START)

    light_state = sylight.get()
    state = systate.get()
    mode = symode.get()
    thr_l, thr_r = sythr.get()

    while True:
        await asyncio.sleep(1)

        prev_state = state
        state = systate.get()
        if prev_state != state:
            if state == systate.ON:
                state_emodji = c.EMODJI_GREEN_CIRCLE
            else:
                state_emodji = c.EMODJI_RED_CIRCLE
            await bot.send_message(CHAT_ID, f"{state_emodji} System is {state} now.")

        if state == systate.ON:
            prev_light_state = light_state
            light_state = sylight.get()
            if prev_light_state != light_state:
                if light_state == sylight.ON:
                    light_state_emodji = c.EMODJI_SUN
                else:
                    light_state_emodji = c.EMODJI_MOON
                await bot.send_message(CHAT_ID, f"{light_state_emodji} Light is {light_state} now.")

        prev_mode = mode
        mode = symode.get()
        if prev_mode != mode:
            if mode == symode.MANUAL:
                mode_emodji = c.EMODJI_MANUAL
            else:
                mode_emodji = c.EMODJI_AUTO  
            await bot.send_message(CHAT_ID, f"{mode_emodji} {mode} mode enabled now.")

        prev_thr_l = thr_l
        prev_thr_r = thr_r
        thr_l, thr_r = sythr.get()
        if (prev_thr_l != thr_l) or (prev_thr_r != thr_r):
            await bot.send_message(CHAT_ID, f"{c.EMODJI_CHECKMARK} Thresholds are {thr_l} and {thr_r} now.")

async def send_on_frames():
    await asyncio.sleep(c.BOT_DELAY_ON_START)

    while True:
        await asyncio.sleep(1)

        files = sorted(syfiles.frames_dpath.glob(f"frame*-.{c.PICTURE_EXT}"))
        if len(files) > 0:
            fpath = files[0]
            dt, level_l, level_r, thr_l, thr_r, reason = syfiles.path2metadata(fpath)
            dt_str = sydt.get_str(dt, pattern='nice')
            
            if reason == 'save_frame':
                caption = f"{c.EMODJI_FRAME} Frame"
            elif reason == 'update_save_ref_frame':
                caption = f"{c.EMODJI_FRAME} Reference frame updated"
            elif reason == 'set_glass_on':
                caption = f"{c.EMODJI_GREEN_CIRCLE} Glass ON"
            elif reason == 'set_glass_off':
                caption = f"{c.EMODJI_RED_CIRCLE} Glass OFF"
            elif reason == 'single':
                caption = f"{c.EMODJI_ALONE} Person ALONE"
            else:
                continue

            caption = f"{caption}\nThresholds: {level_l} ({thr_l}), {level_r} ({thr_r})\nTimestamp: {dt_str}"
            await send_frame(fpath, caption)

@dp.message(Command('start'))
async def cmd__start(message: Message):
    if not await is_from_group(message, notify=True):
        return

    await message.reply(f"{c.EMODJI_START} Welcome!\nUse /help to show available commands.")

@dp.message(Command('help'))
async def cmd__help(message: Message):
    if not await is_from_group(message, notify=True):
        return

    bot_public_cmds_text = "\n".join([f"{cmd} - {description}" for (cmd, description) in bot_public_cmds])
    bot_admin_cmds_text = "\n".join([f"{cmd} - {description}" for (cmd, description) in bot_admin_cmds])
    text = f"{c.EMODJI_GLASS} I am Smart Glass Bot.\n\nPublic commands:\n{bot_public_cmds_text}\n\nAdmin commands:\n{bot_admin_cmds_text}"
    await message.reply(text)

@dp.message(Command('state'))
async def cmd__state(message: Message):
    if not await is_from_group(message):
        return

    t_cpu = sytemp.get()

    state = systate.get()
    if state == systate.ON:
        state_emodji = c.EMODJI_GREEN_CIRCLE
    else:
        state_emodji = c.EMODJI_RED_CIRCLE

    if state == systate.OFF:
        light_state = "unknown"
        light_state_emodji = c.EMODJI_WARNING
    else:
        light_state = sylight.get()
        if light_state == sylight.ON:
            light_state_emodji = c.EMODJI_SUN
        else:
            light_state_emodji = c.EMODJI_MOON

    mode = symode.get()
    if mode == symode.MANUAL:
        mode_emodji = c.EMODJI_MANUAL
    else:
        mode_emodji = c.EMODJI_AUTO  

    glstate = syglstate.get()
    if glstate == syglstate.ON:
        glstate_emodji = c.EMODJI_GREEN_CIRCLE
    else:
        glstate_emodji = c.EMODJI_RED_CIRCLE

    thr_l, thr_r = sythr.get()

    text = (f"CPU temp: {t_cpu:.1f} C\n"
            f"Thresholds: {thr_l}, {thr_r}\n\n"
            f"{state_emodji} System: {state}\n"
            f"{light_state_emodji} Light: {light_state}\n"
            f"{mode_emodji} Mode: {mode}\n"
            f"{glstate_emodji} Glass: {glstate}")

    await message.reply(text)

@dp.message(Command('frame'))
async def cmd__frame(message: Message):
    if not await is_from_group(message):
        return

    if not await system_is_on(message, notify=True):
        return

    sycam.save_frame_request()
    await message.reply(f"{c.EMODJI_REQUEST} Frame requested.")

@dp.message(Command('ref'))
async def cmd__ref(message: Message):
    if not await is_from_group(message):
        return

    if not syfiles.reference_frame_fpath.is_file():
        await message.answer(f"{c.EMODJI_WARNING} No reference frames found.")
        return

    dt_str = sydt.get_str(pattern='nice')
    caption = f"{c.EMODJI_FRAME} Reference frame\nTimestamp: {dt_str}"
    await send_frame(syfiles.reference_frame_fpath, caption, rename=False)

@dp.message(Command('on'))
async def cmd__on(message: Message):
    if not await is_from_group(message):
        return

    if not await is_from_admin(message, notify=True):
        return

    state = systate.get()
    if state == systate.ON:
        await message.reply(f"{c.EMODJI_WARNING} System is already {state}.")
        return

    systate.set_request(systate.ON)
    await message.reply(f"{c.EMODJI_REQUEST} Turning system {systate.ON} requested.")

@dp.message(Command('off'))
async def cmd__off(message: Message):
    if not await is_from_group(message):
        return

    if not await is_from_admin(message, notify=True):
        return

    state = systate.get()
    if state == systate.OFF:
        await message.reply(f"{c.EMODJI_WARNING} System is already {state}.")
        return

    systate.set_request(systate.OFF)
    await message.reply(f"{c.EMODJI_REQUEST} Turning system {systate.OFF} requested.")

@dp.message(Command('manual'))
async def cmd__manual(message: Message):
    if not await is_from_group(message):
        return

    if not await is_from_admin(message, notify=True):
        return

    mode = symode.get()
    if mode == symode.MANUAL:
        await message.reply(f"{c.EMODJI_WARNING} Mode is already {mode}.")
        return

    symode.set_request(symode.MANUAL)
    await message.reply(f"{c.EMODJI_REQUEST} {symode.MANUAL} mode requested.")

@dp.message(Command('auto'))
async def cmd__auto(message: Message):
    if not await is_from_group(message):
        return

    if not await is_from_admin(message, notify=True):
        return

    mode = symode.get()
    if mode == symode.AUTO:
        await message.reply(f"{c.EMODJI_WARNING} Mode is already {mode}.")
        return

    symode.set_request(symode.AUTO)
    await message.reply(f"{c.EMODJI_REQUEST} {symode.AUTO} mode requested.")

@dp.message(Command('glon'))
async def cmd__glon(message: Message):
    if not await is_from_group(message):
        return

    if not await is_from_admin(message, notify=True):
        return

    if not await system_is_on(message, notify=True):
        return

    if not await mode_is_manual(message, notify=True):
        return

    glstate = syglstate.get()
    if glstate == syglstate.ON:
        await message.reply(f"{c.EMODJI_WARNING} Glass is already {glstate}.")
        return

    syglstate.set_request(syglstate.ON)
    await message.reply(f"{c.EMODJI_REQUEST} Turning glass {syglstate.ON} requested.")

@dp.message(Command('gloff'))
async def cmd__gloff(message: Message):
    if not await is_from_group(message):
        return

    if not await is_from_admin(message, notify=True):
        return

    if not await system_is_on(message, notify=True):
        return

    if not await mode_is_manual(message, notify=True):
        return

    glstate = syglstate.get()
    if glstate == syglstate.OFF:
        await message.reply(f"{c.EMODJI_WARNING} Glass is already {glstate}.")
        return

    syglstate.set_request(syglstate.OFF)
    await message.reply(f"{c.EMODJI_REQUEST} Turning glass {syglstate.OFF} requested.")

@dp.message(Command('updateref'))
async def cmd__updateref(message: Message):
    if not await is_from_group(message):
        return

    if not await is_from_admin(message, notify=True):
        return

    if not await system_is_on(message, notify=True):
        return

    sycam.update_save_reference_frame_request()
    await message.reply(f"{c.EMODJI_REQUEST} Update reference frame requested.")

@dp.message(Command('updatethr'))
async def cmd__updatethr(message: Message):
    if not await is_from_group(message):
        return

    if not await is_from_admin(message, notify=True):
        return

    if not await system_is_on(message, notify=True):
        return
    
    try:
        text = message.text
        l = text.split()
        if len(l) != 2 or l[0] != '/updatethr':
            raise Exception
        l = l[1].split(',')
        thr_l = int(l[0])
        thr_r = int(l[1])
    except:
        await message.reply(f"{c.EMODJI_WARNING} Invalid arguments.")
        return

    sythr.update_thresholds_request(thr_l, thr_r)
    await message.reply(f"{c.EMODJI_REQUEST} Update thresholds requested.")

#@dp.message()
#async def cmd__any(message: Message):
    #await message.answer("Answered")

async def main():
    await bot.send_message(CHAT_ID, f"{c.EMODJI_CHECKMARK} Smart Glass Bot started.")

    asyncio.create_task(send_ping())
    asyncio.create_task(send_on_states())
    asyncio.create_task(send_on_frames())

    await dp.start_polling(bot)
    

if __name__ == '__main__':
    syfiles.prepare_folders(clean=False)
    asyncio.run(main())

import asyncio
from datetime import timedelta
from os import getenv
from pathlib import Path
import sys
import traceback

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton

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

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=f'{c.EMODJI_INFO} STATE'),
            KeyboardButton(text=f'{c.EMODJI_FRAME} FRAME')
        ],
        [
            KeyboardButton(text=f'{c.EMODJI_STATS} STATISTICS')
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Type command...",
)

bot_public_cmds = [
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

async def try_send_msg(dest_id, text):
    try:
        await bot.send_message(dest_id, text, reply_markup=main_kb)
    except:
        print(f"Failed to send message!\nText:\n{text}\n")

async def try_reply(msg, text):
    try:
        await msg.reply(text, reply_markup=main_kb)
    except:
        print(f"Failed to reply!\nText:\n{text}\n")

async def is_from_group(msg, notify=False):
    if str(msg.chat.id) == CHAT_ID:
        return True

    if notify:
        await try_reply(msg, f"{c.EMODJI_WARNING} Bot can be used in its dedicated group only.")

    return False

async def is_from_admin(msg, notify=False):
    if str(msg.from_user.id) == ADMIN_ID:
        return True

    if notify:
        await try_reply(msg, f"{c.EMODJI_WARNING} Command can be used by admin only.")

    return False

async def system_is_on(msg, notify=False):
    state = systate.get()
    if state == systate.ON:
        return True

    if notify:
        await try_reply(msg, f"{c.EMODJI_WARNING} System is {systate.OFF}.\nUse command /on to turn it {systate.ON} first.")

    return False

async def mode_is_manual(msg, notify=False):
    mode = symode.get()
    if mode == symode.MANUAL:
        return True

    if notify:
        await try_reply(msg, f"{c.EMODJI_WARNING} Mode is {symode.AUTO}.\nUse command /manual to enable {symode.MANUAL} mode first.")

    return False

async def send_frame(fpath, caption, rename=True):
    file = FSInputFile(fpath)
     
    try:
        await bot.send_photo(CHAT_ID, file, caption=caption)
    except:
        return

    if rename:
        fname_new = fpath.name.replace('-', '')
        fpath_new = fpath.parent / fname_new
        syfiles.move_file(fpath, fpath_new)

async def send__ping():
    await asyncio.sleep(c.BOT_DELAY_ON_START)

    text = "Ping"
    delta = timedelta(minutes=1)
    next_dt = sydt.now() - delta

    while True:
        if sydt.now() > next_dt:
            next_dt = sydt.now() + delta
            await try_send_msg(ADMIN_ID, text)

        await asyncio.sleep(c.BOT_DELAY_LOOP)

async def send__states_update():
    await asyncio.sleep(c.BOT_DELAY_ON_START)

    light_state = sylight.get()
    state = systate.get()
    mode = symode.get()
    thr_l, thr_r = sythr.get()

    while True:
        prev_state = state
        state = systate.get()
        if prev_state != state:
            if state == systate.ON:
                state_emodji = c.EMODJI_GREEN_CIRCLE
            else:
                state_emodji = c.EMODJI_RED_CIRCLE
            await try_send_msg(CHAT_ID, f"{state_emodji} System is {state} now.")

        if state == systate.ON:
            prev_light_state = light_state
            light_state = sylight.get()
            if prev_light_state != light_state:
                if light_state == sylight.ON:
                    light_state_emodji = c.EMODJI_SUN
                else:
                    light_state_emodji = c.EMODJI_MOON
                await try_send_msg(CHAT_ID, f"{light_state_emodji} Light is {light_state} now.")

        prev_mode = mode
        mode = symode.get()
        if prev_mode != mode:
            if mode == symode.MANUAL:
                mode_emodji = c.EMODJI_MANUAL
            else:
                mode_emodji = c.EMODJI_AUTO  
            await try_send_msg(CHAT_ID, f"{mode_emodji} {mode} mode enabled now.")

        prev_thr_l = thr_l
        prev_thr_r = thr_r
        thr_l, thr_r = sythr.get()
        if (prev_thr_l != thr_l) or (prev_thr_r != thr_r):
            await try_send_msg(CHAT_ID, f"{c.EMODJI_CHECKMARK} Thresholds are {thr_l} and {thr_r} now.")
        
        await asyncio.sleep(c.BOT_DELAY_LOOP)

async def send__new_frames():
    await asyncio.sleep(c.BOT_DELAY_ON_START)

    while True:
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

        await asyncio.sleep(c.BOT_DELAY_LOOP)

@dp.message(Command('start'))
async def cmd__start(msg: Message):
    await try_reply(msg, f"{c.EMODJI_START} Welcome!\nUse /help to show available commands.")

@dp.message(Command('help'))
async def cmd__help(msg: Message):
    bot_public_cmds_text = "\n".join([f"{cmd} - {description}" for (cmd, description) in bot_public_cmds])
    bot_admin_cmds_text = "\n".join([f"{cmd} - {description}" for (cmd, description) in bot_admin_cmds])
    text = f"{c.EMODJI_GLASS} I am Smart Glass Bot.\n\nPublic commands:\n{bot_public_cmds_text}\n\nAdmin commands:\n{bot_admin_cmds_text}"
    await try_reply(msg, text)

@dp.message(Command('state'))
async def cmd__state(msg: Message):
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

    await try_reply(msg, text)

@dp.message(Command('frame'))
async def cmd__frame(msg: Message):
    if not await is_from_group(msg):
        return

    if not await system_is_on(msg, notify=True):
        return

    sycam.save_frame_request()
    await try_reply(msg, f"{c.EMODJI_REQUEST} Frame requested.")

@dp.message(Command('ref'))
async def cmd__ref(msg: Message):
    if not await is_from_group(msg):
        return

    if not syfiles.reference_frame_fpath.is_file():
        await try_reply(msg, f"{c.EMODJI_WARNING} No reference frames found.")
        return

    dt_str = sydt.get_str(pattern='nice')
    caption = f"{c.EMODJI_FRAME} Reference frame\nTimestamp: {dt_str}"
    await send_frame(syfiles.reference_frame_fpath, caption, rename=False)

@dp.message(Command('on'))
async def cmd__on(msg: Message):
    if not await is_from_group(msg):
        return

    if not await is_from_admin(msg, notify=True):
        return

    state = systate.get()
    if state == systate.ON:
        await try_reply(msg, f"{c.EMODJI_WARNING} System is already {state}.")
        return

    systate.set_request(systate.ON)
    await try_reply(msg, f"{c.EMODJI_REQUEST} Turning system {systate.ON} requested.")

@dp.message(Command('off'))
async def cmd__off(msg: Message):
    if not await is_from_group(msg):
        return

    if not await is_from_admin(msg, notify=True):
        return

    state = systate.get()
    if state == systate.OFF:
        await try_reply(msg, f"{c.EMODJI_WARNING} System is already {state}.")
        return

    systate.set_request(systate.OFF)
    await try_reply(msg, f"{c.EMODJI_REQUEST} Turning system {systate.OFF} requested.")

@dp.message(Command('manual'))
async def cmd__manual(msg: Message):
    if not await is_from_group(msg):
        return

    if not await is_from_admin(msg, notify=True):
        return

    mode = symode.get()
    if mode == symode.MANUAL:
        await try_reply(msg, f"{c.EMODJI_WARNING} Mode is already {mode}.")
        return

    symode.set_request(symode.MANUAL)
    await try_reply(msg, f"{c.EMODJI_REQUEST} {symode.MANUAL} mode requested.")

@dp.message(Command('auto'))
async def cmd__auto(msg: Message):
    if not await is_from_group(msg):
        return

    if not await is_from_admin(msg, notify=True):
        return

    mode = symode.get()
    if mode == symode.AUTO:
        await try_reply(msg, f"{c.EMODJI_WARNING} Mode is already {mode}.")
        return

    symode.set_request(symode.AUTO)
    await try_reply(msg, f"{c.EMODJI_REQUEST} {symode.AUTO} mode requested.")

@dp.message(Command('glon'))
async def cmd__glon(msg: Message):
    if not await is_from_group(msg):
        return

    if not await is_from_admin(msg, notify=True):
        return

    if not await system_is_on(msg, notify=True):
        return

    if not await mode_is_manual(msg, notify=True):
        return

    glstate = syglstate.get()
    if glstate == syglstate.ON:
        await try_reply(msg, f"{c.EMODJI_WARNING} Glass is already {glstate}.")
        return

    syglstate.set_request(syglstate.ON)
    await try_reply(msg, f"{c.EMODJI_REQUEST} Turning glass {syglstate.ON} requested.")

@dp.message(Command('gloff'))
async def cmd__gloff(msg: Message):
    if not await is_from_group(msg):
        return

    if not await is_from_admin(msg, notify=True):
        return

    if not await system_is_on(msg, notify=True):
        return

    if not await mode_is_manual(msg, notify=True):
        return

    glstate = syglstate.get()
    if glstate == syglstate.OFF:
        await try_reply(msg, f"{c.EMODJI_WARNING} Glass is already {glstate}.")
        return

    syglstate.set_request(syglstate.OFF)
    await try_reply(msg, f"{c.EMODJI_REQUEST} Turning glass {syglstate.OFF} requested.")

@dp.message(Command('updateref'))
async def cmd__updateref(msg: Message):
    if not await is_from_group(msg):
        return

    if not await is_from_admin(msg, notify=True):
        return

    if not await system_is_on(msg, notify=True):
        return

    sycam.update_save_reference_frame_request()
    await try_reply(msg, f"{c.EMODJI_REQUEST} Update reference frame requested.")

@dp.message(Command('updatethr'))
async def cmd__updatethr(msg: Message):
    if not await is_from_group(msg):
        return

    if not await is_from_admin(msg, notify=True):
        return

    if not await system_is_on(msg, notify=True):
        return
    
    try:
        l = msg.text.split()
        if len(l) != 2 or l[0] != '/updatethr':
            raise Exception
        l = l[1].split(',')
        thr_l = int(l[0])
        thr_r = int(l[1])
    except:
        await try_reply(msg, f"{c.EMODJI_WARNING} Invalid arguments.")
        return

    sythr.update_thresholds_request(thr_l, thr_r)
    await try_reply(msg, f"{c.EMODJI_REQUEST} Update thresholds requested.")

#@dp.message()
#async def cmd__any(msg: Message):
    #await try_reply(msg, "Answered")

async def main():
    start_text = "Smart Glass Bot started"

    await try_send_msg(ADMIN_ID, f"{c.EMODJI_CHECKMARK} {start_text}.")

    asyncio.create_task(send__ping())
    asyncio.create_task(send__states_update())
    asyncio.create_task(send__new_frames())

    await dp.start_polling(bot)


if __name__ == '__main__':
    syfiles.prepare_folders(clean=False)
    asyncio.run(main())

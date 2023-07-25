import asyncio
import json
import math
import os
import re
import time

import cv2
import humanize
from pyrogram import Client
from pyrogram.handlers import MessageHandler
from ffmpeg import Progress
from ffmpeg.asyncio import FFmpeg
import gvar

msg_id = None
chat_id = None

async def commonmessage(client, message):
    global msg_id, chat_id

    if message.from_user is None:
        return

    if message.text is None:
        return

    textmsg = message.text

    if ".sms" in textmsg:
        link = (re.search(r"(?P<url>https?://\S+)", textmsg).group("url"))
        if "?" in link:
            link = link.split('?')[0]

        msg_id = int(link.split("/")[-1])
        if any(c.isalpha() for c in link.split("/")[-2]):
            chat_id = link.split("/")[-2]
        else:
            chat_id = int('-100' + str(link.split("/")[-2]))

        event = await app.get_messages(chat_id, msg_id)

        await sender_single_alt(event)


async def sender_single_alt(mesgsingle):
    print("sender_single_alt")
    messagestatus = "sender_single_alt"
    singlefile = None
    try:
        singlefile = await app.download_media(
            mesgsingle,
            progress=progress_download_for_pyrogram,
            progress_args=(
                time.time(),
                messagestatus,
            )
        )
    except Exception as err:
        messerr = f"There is error when {mesgsingle.chat.id}, chat_id = {mesgsingle.id} \n Error= {err}"
        print(messerr)
        await asyncio.sleep(4)

    if str(singlefile).lower().split(".")[-1] in ['mkv', 'flv', 'mp4', 'webm', 'mpe4', 'mpeg', 'mov']:
        if str(singlefile).split(".")[-1] not in ['mp4', 'mov']:
            singlefile = await convert_to_mp4(singlefile)

    if singlefile is not None and os.path.exists(singlefile):
        await asyncio.sleep(1)

        data = video_metadata(singlefile)
        duration = data["duration"]

        filename = os.path.basename(singlefile)
        workdir = os.path.dirname(singlefile)
        filenamewithoutext = os.path.splitext(filename)[0]

        fullpathjpg = os.path.join(workdir, filenamewithoutext + "_thumb.jpg")

        try:
            thumb_path = save_frame_from_video(singlefile, duration, fullpathjpg)
        except Exception as e:
            print(e)
            thumb_path = None

        try:
            fileid = await wrapper_send_video(data, mesgsingle, singlefile, thumb_path)
        except Exception as fnien:
            print(f"Error when UploadMediaSingle = {fnien}")

        await asyncio.sleep(3)


async def wrapper_send_video(data, mesgsingle, singlefile, thumb_path):
    duration = data["duration"]
    width = data["width"]
    height = data["height"]

    filename = os.path.basename(singlefile)

    caption = None
    if mesgsingle.caption is not None:
        caption = mesgsingle.caption

    return await app.send_video(
        "me",
        singlefile,
        caption=caption,
        thumb=thumb_path,
        duration=duration,
        width=width,
        height=height,
        progress=progress_bar_upload_single,
        progress_args=(
            time.time(),
            f"sending movie file {filename} ",
        ),
    )


async def progress_download_for_pyrogram(current, total, start, choice_single_album="single"):

    FINISHED_PROGRESS_STR = "█"
    UN_FINISHED_PROGRESS_STR = ""
    DOWNLOAD_LOCATION = "./app/"

    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        status = DOWNLOAD_LOCATION + "/status.json"
        if os.path.exists(status):
            with open(status, 'r+') as f:
                statusMsg = json.load(f)
                if not statusMsg["running"]:
                    app.stop_transmission()
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "{0}, **[{1}{2}]** `| {3}%`, ".format(
            choice_single_album,
            ''.join([FINISHED_PROGRESS_STR for _ in
                     range(math.floor(percentage / 10))]),
            ''.join([UN_FINISHED_PROGRESS_STR for _ in
                     range(10 - math.floor(percentage / 10))]),
            round(percentage, 2))

        tmp = progress + "GROSSS: {0} of {1}, Speed: {2}/s,  ETA: {3}".format(
            humanize.naturalsize(current),
            humanize.naturalsize(total),
            humanize.naturalsize(speed),
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        print(tmp)

async def progress_bar_upload_single(current, total, start, tambahan=""):

    DOWNLOAD_LOCATION = "./app/"
    now = time.time()
    diff = now - start

    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        status = DOWNLOAD_LOCATION + "/status.json"
        if os.path.exists(status):
            with open(status, 'r+') as f:
                statusMsg = json.load(f)
                if not statusMsg["running"]:
                    app.stop_transmission()
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        # elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "{0} , {1}% , ".format(
            tambahan,
            round(percentage, 2),
        )

        tmp = progress + "GROSSS: {0} of {1}, Speed: {2}/s,  ETA: {3}".format(
            humanize.naturalsize(current),
            humanize.naturalsize(total),
            humanize.naturalsize(speed),
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        print(tmp)

def video_metadata(videofile):
    print("video_metadata")
    data = {}
    try:
        vcap = cv2.VideoCapture(videofile)
        if vcap.isOpened():
            width = round(vcap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = round(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = vcap.get(cv2.CAP_PROP_FPS)
            frame_count = vcap.get(cv2.CAP_PROP_FRAME_COUNT)
            print(frame_count)
            print(fps)
            duration = round(frame_count / fps)
            data = {'width': width, 'height': height, 'duration': duration}
            vcap.release()
    except Exception as err:
        print(f"terjadi error cv2.VideoCapture {err}")

    return data

def save_frame_from_video(video_path, durationsecond, frame_file_path):
    print("save_frame_from_video")
    try:
        if os.path.exists(f'{frame_file_path}'):
            return f'{frame_file_path}'
        time_stamp = int(durationsecond) / 2
        time_stampmili = int(time_stamp * 1000)
        # print(time_stampmili)
        # out = datetime.now().isoformat("_", "seconds") + ".jpg"
        vidcap = cv2.VideoCapture(video_path)

        vidcap.set(cv2.CAP_PROP_POS_MSEC, time_stampmili)

        success, image = vidcap.read()

        # save image to temp file
        cv2.imwrite(frame_file_path, image)

        vidcap.release()
    except Exception as erhr:
        print(erhr)

    if os.path.exists(f'{frame_file_path}'):
        return f'{frame_file_path}'
    else:
        return None

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
          ((str(hours) + "h, ") if hours else "") + \
          ((str(minutes) + "m, ") if minutes else "") + \
          ((str(seconds) + "s, ") if seconds else "")
    return tmp[:-2]

async def convert_to_mp4(input_file):
    print("convert_to_mp4")
    filename = os.path.basename(input_file)
    workdir = os.path.dirname(input_file)
    filenamewithoutext = os.path.splitext(filename)[0]
    fullpathoutput = os.path.join(workdir, filenamewithoutext + "_converted.mp4")
    file_stats = os.stat(input_file)
    human_size = humanize.naturalsize(file_stats.st_size)

    try:
        ffmpeg = (
            FFmpeg()
            .option("y")
            .input(input_file)
            .output(fullpathoutput, vcodec="copy")
        )
        @ffmpeg.on("progress")
        def the_progress(progress: Progress):
            print(f"Converting file={filename}, size={human_size}.\n  {progress}")

        await ffmpeg.execute()
    except Exception as fnn:
        print(fnn)

    return fullpathoutput




app = Client(
    name="useraccount",
    app_version="Telegram Desktop 4.5.3 x64",
    device_model="Windows 10",
    api_id=gvar.api_id,
    api_hash=gvar.api_hash
)
app.add_handler(MessageHandler(commonmessage, None))

app.run()
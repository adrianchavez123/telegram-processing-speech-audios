import schedule
import time
import requests
import csv
import os, json
import telebot
import urllib.request
from dotenv import load_dotenv
from audio_helper import get_format, save_audio, analyze_audio
from audio_details import save_audio_deliver
from datetime import datetime
import logging

load_dotenv()
logging.basicConfig(filename='logs/test.log', level = logging.DEBUG,
format='%(asctime)s:%(levelname)s:%(message)s')

telegram_token = os.environ['TELEGRAM_TOKEN']
word_count_service = os.environ.get('WORD_COUNTER_SERVICE', 'http://localhost:5000/api')
close_pass_due_date_end_point = os.environ.get('CLOSE_PASS_DUE_DATE_END_POINT','/assignments/close-pass-due-date')
pending_notifications_end_point = os.environ.get('PENDING_NOTIFICATIONS_END_POINT','/assignments/pending-notifications')
delete_notifications_sent_end_point = os.environ.get('DELETE_NOTIFICATIONS_SENT_END_POINT','/assignments/delete-notification')
analyze_speech_method = os.environ.get('ANALYZE_SPEECH_METHOD', 'AMPLITUDE_TO_DB')
audio_jobs = os.environ.get('AUDIO_JOBS_FILE', './audio_jobs.csv')

bot = telebot.TeleBot(telegram_token)

def close_pass_due_date_assignments():
    try:
        logging.info("executing close_pass_due_date_assignments()")
        r = requests.get(word_count_service + close_pass_due_date_end_point)
        return r.json()
    except Exception as e:
        logging.warning(f"close assignments failed, error: {e}")

def delete_notification_template(file_name):
    logging.info(f"executing delete notification template {file_name}")
    r = requests.get(word_count_service + delete_notifications_sent_end_point + '/' + file_name)
    return r.json()

def notify_group_new_assignment():
    try:
        logging.debug(f"executing notify_group_new_assignment ")
        r = requests.get(word_count_service + pending_notifications_end_point)
        data = r.json()

        for notification in data['notifications']:
            file_name = notification['fileName']
            assignment_title = notification['assignment_title']
            description = notification['description']
            due_date = notification['due_date']
            image = notification['image']
            students = notification['students']
            for student_id in students:
                send_notification(assignment_title, description, due_date, image, student_id)

            delete_notification_template(file_name)
    except Exception as e:
        logging.warning(f"Notification deliver failed, error: {e}")

def send_notification(assignment_title, description, due_date, image, student_id):
    logging.debug("sending notification")
    if image:
        logging.debug("sending notification with image")
        chucks = image.split('.')
        extension = chucks[len(chucks)-1]
        with urllib.request.urlopen(image) as url:
            with open(f'./imagestemp.{extension}', 'wb') as f:
                f.write(url.read())
        photo = open(f'./imagestemp.{extension}', 'rb')
        logging.debug(f"sending notification: {assignment_title},{description}")
        bot.send_photo(student_id, photo, getText(assignment_title, description, due_date), parse_mode = "Markdown")
        os.remove(f'./imagestemp.{extension}')
    else :
        logging.debug(f"sending notification: {assignment_title},{description}")
        bot.send_message(student_id, getText(assignment_title, description, due_date), parse_mode = "Markdown")

def getText(assignment_title, description, due_date):
    date_message = ""
    if  due_date:  date_message = f"Enviar antes del final del día: _{due_date}_"
    return f"_Nueva Tarea_: *{assignment_title}*\n {description}.\n {date_message}"

def process_audios():
    logging.debug(" processing audio files")
    deliver_failures = []
    with open(audio_jobs) as fp:
        reader = csv.reader(fp, delimiter=",")
        next(reader, None)
        for row in reader:
            try:
                student_id = row[0]
                date_timestamp = row[1]
                file_unique_id = row[2]
                mime_type = row[3]
                file_id = row[4]
                date = datetime.fromtimestamp(int(date_timestamp))
                arrive_at = date.strftime('%Y-%m-%d')
                logging.info(f"processing audio deliver (student_id={student_id} - {arrive_at} - {file_id} ).")
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                sound, file_name = save_audio(downloaded_file, student_id, date_timestamp, file_unique_id, mime_type)
                words_amount, text = analyze_audio(sound, analyze_speech_method, file_name)
                response = save_audio_deliver(student_id, file_info.file_path, words_amount, text,arrive_at)
            except Exception as e:
                logging.warning(f"audio deliver (student_id={student_id} - {file_id} ) failed. \nerror: {e}")
                deliver_failures.append(row)

    # update csv
    with open(audio_jobs, "wt") as fp:
        writer = csv.writer(fp, delimiter=",")
        writer.writerow(["student_id", "date", "file_unique_id", "mime_type", "file_id"])
        writer.writerows(deliver_failures)
        logging.info(f"updating {audio_jobs}")

# CRONJOBS #
# runs every 10 seconds, if a new assignment was created trigger notify group members
#schedule.every(10).seconds.do(notify_group_new_assignment)

# runs at 23:50 and closes assignments where its due date has been reached
schedule.every().day.at("23:50").do(close_pass_due_date_assignments)

# heavy task that process the audios
schedule.every().day.at("02:00").do(process_audios)

while True:
    schedule.run_pending()
    time.sleep(1)

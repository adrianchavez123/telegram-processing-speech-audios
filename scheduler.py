import schedule
import time
import requests
import os, json
import telebot
import urllib.request
from dotenv import load_dotenv

load_dotenv()

telegram_token = os.environ['TELEGRAM_TOKEN']
word_count_service = os.environ.get('WORD_COUNTER_SERVICE', 'http://localhost:5000/api')
close_pass_due_date_end_point = os.environ.get('CLOSE_PASS_DUE_DATE_END_POINT','/assignments/close-pass-due-date')
pending_notifications_end_point = os.environ.get('PENDING_NOTIFICATIONS_END_POINT','/assignments/pending-notifications')
delete_notifications_sent_end_point = os.environ.get('DELETE_NOTIFICATIONS_SENT_END_POINT','/assignments/delete-notification')

bot = telebot.TeleBot(telegram_token)

def close_pass_due_date_assignments():
    r = requests.get(word_count_service + close_pass_due_date_end_point)
    print(r.json())
    return r.json()

def delete_notification_template(file_name):
    r = requests.get(word_count_service + delete_notifications_sent_end_point + '/' + file_name)
    return r.json()

def notify_group_new_assignment():
    r = requests.get(word_count_service + pending_notifications_end_point)
    data = r.json()
    try:
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
        print(e)
        print("Notification deliver failed")

def send_notification(assignment_title, description, due_date, image, student_id):
    if image:
        chucks = image.split('.')
        extension = chucks[len(chucks)-1]
        with urllib.request.urlopen(image) as url:
            with open(f'./imagestemp.{extension}', 'wb') as f:
                f.write(url.read())
        photo = open(f'./imagestemp.{extension}', 'rb')
        bot.send_photo(student_id, photo, getText(assignment_title, description, due_date), parse_mode = "Markdown")
        os.remove(f'./imagestemp.{extension}')
    else :
        bot.send_message(student_id, getText(assignment_title, description, due_date), parse_mode = "Markdown")

def getText(assignment_title, description, due_date):
    date_message = ""
    if  due_date:  date_message = f"Enviar antes del final del día: _{due_date}_"
    return f"_Nueva Tarea_: *{assignment_title}*\n {description}.\n {date_message}"

schedule.every(10).seconds.do(notify_group_new_assignment)
schedule.every().day.at("23:50").do(close_pass_due_date_assignments)

while True:
    schedule.run_pending()
    time.sleep(1)

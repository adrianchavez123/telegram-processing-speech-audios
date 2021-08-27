import os, json
import pandas as pd
import telebot

telegram_token = os.environ['TELEGRAM_TOKEN']
path = os.environ.get('NOTIFICATIONS_DIRECTORY', './notifications')

bot = telebot.TeleBot(telegram_token)

def read_notification_data_structures(path):
    print(path)
    try:
        json_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.json')]

        for index, js in enumerate(json_files):
            with open(os.path.join(path, js)) as json_file:
                json_text = json.load(json_file)

                assignment_title = json_text['assignment_title']
                description = json_text['description']
                due_date = json_text['due_date']
                image = json_text['image']
                students = json_text['students']
                for student_id in students:
                    send_notification(assignment_title, description, due_date, image, student_id)

                remove_notification_file(os.path.join(path, js))
    except Exception as e:
        print("Sending notifications is not working, make sure the data structure is correct.")
        print(e)

def send_notification(assignment_title, description, due_date, image, student_id):
    if image:
        photo = open('./images/image.jpeg', 'rb')
        bot.send_photo(student_id, photo, getText(assignment_title, description, due_date), parse_mode = "Markdown")
    else :
        bot.send_message(student_id, getText(assignment_title, description, due_date), parse_mode = "Markdown")

def getText(assignment_title, description, due_date):
    date_message = ""
    if  due_date:  date_message = f"Enviar antes del final del día: _{due_date}_"
    return f"_Nueva Tarea_: *{assignment_title}*\n {description}.\n {date_message}"

def remove_notification_file(file_name):
    try:
        os.remove(file_name)
    except:
        print("Error while deleting file ", file_name)

read_notification_data_structures(path)

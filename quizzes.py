import telebot
from telebot import types
import urllib.request
import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()
log_file = os.environ['LOG_FILE']
logging.basicConfig(filename=log_file, level = logging.INFO,
format='%(asctime)s:%(levelname)s:%(message)s')

telegram_token = os.environ['TELEGRAM_TOKEN']

word_count_service = os.environ.get('WORD_COUNTER_SERVICE', 'http://localhost:5000/api')
questions_endpoint = os.environ.get('QUESTIONS_END_POINT','/questions')
deliver_assignment_answers_endpoint = os.environ.get('DELIVER_QUESTION_ANSWER','/deliver-assignment-answers')


bot = telebot.TeleBot(telegram_token)

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == "/quizz":

        title = None
        exercise_id = None
        questions = None
        question_ids = []
        try:
            logging.info(f" query endpoint: {questions_endpoint}?exercise_id="+"141")
            r = requests.get(word_count_service + questions_endpoint + "?exercise_id=" + "141") #update this
            json_response = r.json()

            if( 'message' in json_response):
                msg = json_response['message']
                if msg == 'No Questions!':
                    logging.warning(f" Response with message error: {msg}")
                    bot.send_message(message.chat.id, f"Tarea recibido. :)")
                    return


            if 'exercise' in json_response:
                title = json_response['exercise']['title']
                exercise_id = json_response['exercise']['id']
                questions = json_response['questions']
            else:
                logging.warning(f" Exit exercise not found.")
                return
        except requests.exceptions.RequestException as e:
            logging.warning(f" Error: {e}")
            bot.send_message(message.chat.id, "No fue posible lanzar el cuestonario.")
        for question in questions:
            question_ids.append(question['question_id'])
        if exercise_id is not None:
            keyboard = types.InlineKeyboardMarkup()

            if len(questions) > 0:
                question_name = questions[0]['question_name']
                question_id = questions[0]['question_id']
                question_ids.remove(question_id)
                str_question_ids = [str(q) for q in question_ids]
                question_ids_joined = '_'.join(str_question_ids)

                if len(questions[0]['options']) > 0:
                    options = questions[0]['options']

                    for option in options:
                        option_name = option['option_name']
                        question_option_id = option['question_option_id']
                        logging.info(f" callback string: {exercise_id},{question_id},{question_option_id},{question_ids_joined}")
                        option_button = types.InlineKeyboardButton(text=option_name,callback_data=f"{exercise_id},{question_id},{question_option_id},{question_ids_joined}")
                        keyboard.add(option_button)

                    bot.send_message(message.from_user.id, question_name, reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "termino tu evaluación gracias por participar.")

@bot.callback_query_handler(func=lambda call:True)
def callback_worker(call):
    logging.info(f" callback worker executed.")
    exercise_id,question_id,question_option_id,next_questions_ids =  split_data_parts(call.data)
    next_questions_ids_list = next_questions_ids.split('_')
    try:
        logging.info(f" Saving answer of question id:{question_id}, exerciseid: {exercise_id}, option selected: {question_option_id} ")
        r = requests.post(word_count_service + deliver_assignment_answers_endpoint, json={
        "deliver_assignment_id": "1",#update later
        "deliver_assignment_answer_id": None,
        "question_id": question_id,
        "question_option_id": question_option_id,
        })
        json_response = r.json()

    except requests.exceptions.RequestException as e:
        logging.warning(f" Error saving the answer: {e}")
        bot.send_message(call.from_user.id, f"La pregunta no pudo ser guarda, por favor intentar más tarde.")

    if(not question_saved(json_response, call)):
        logging.warning(f"Stop execution response with error message")
        return

    if next_questions_ids is not None and next_questions_ids:
        r = requests.get(word_count_service + questions_endpoint + "?exercise_id=" + exercise_id)
        json_response = r.json()
        questions = json_response['questions']
        next_question_id = None
        question_name = None
        options = None
        for question in questions:
            if( str(question['question_id']) in next_questions_ids_list):
                next_question_id = str(question['question_id'])
                question_name = question['question_name']
                options = question['options']
                break

        if options is not None:
            keyboard = types.InlineKeyboardMarkup()
            next_questions_ids_list.remove(next_question_id)
            question_ids_joined = '_'.join(next_questions_ids_list)

            for option in options:
                option_name = option['option_name']
                question_option_id = option['question_option_id']
                logging.info(f"Callback string next question: {exercise_id},{next_question_id},{question_option_id},{question_ids_joined}")
                option_button = types.InlineKeyboardButton(text=option_name, callback_data=f"{exercise_id},{next_question_id},{question_option_id},{question_ids_joined}")
                keyboard.add(option_button)

            bot.send_message(call.from_user.id,question_name, reply_markup=keyboard)
    else:
        logging.info(f" Quizz completed.")
        bot.send_message(call.message.chat.id, "termino tu evaluación gracias por participar")


def split_data_parts(data):
    logging.info(f" Split callback data.")
    parts = data.split(',')
    exercise_id = parts[0]
    question_id = parts[1]
    question_option_id = parts[2]
    next_questions_ids = parts[3]
    return exercise_id,question_id,question_option_id,next_questions_ids


def question_saved(json_response, message_handler):
    logging.info(f" Call question_save() validate response message")
    if( 'message' in json_response):
        msg = json_response['message']
        if 'You need to deliver your audio first to save a question.' in msg:
            logging.warning(f"End quizz and audio deliver was not found.")
            bot.send_message(message_handler.from_user.id, f"Tienes que enviar un audio antes de contestar el cuestonario.")
            return False
        elif 'You can not answer the question only once.' in msg:
            logging.warning(f"End quizz, it was answered in the past.")
            bot.send_message(message_handler.from_user.id, f"Solo puedes responder una vez la pregunta.")
            return False
    return True


bot.polling(none_stop=True, interval=0)

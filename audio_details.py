import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(filename='/home/ec2-user/auto-subscribe-students/logs/test.log', level = logging.DEBUG,
format='%(asctime)s:%(levelname)s:%(message)s')

word_count_service = os.environ.get('WORD_COUNTER_SERVICE', 'http://localhost:5000/api')
deliver_assignment_endpoint = os.environ.get('DELIVER_ASSIGNMENT_ENDPOINT','/deliver-assignments')
get_last_assignment_id = os.environ.get('GET_LAST_ASSIGNMENT_ID','/assignments/last-assignment')
telegram_token = os.environ['TELEGRAM_TOKEN']
telegram_audio_endpoint = os.environ.get('TELEGRAM_AUDIO_ENDPOINT','https://api.telegram.org/file/bot')

def save_audio_deliver(student_id, file_name, total_words_detected, speech_to_text, date):
	try:
		logging.info(f"executing save_audio_deliver {student_id} - {file_name}")
		assignment_id, verb, deliver_assignment_id = get_assignment_id(student_id);
		r = None
		if(verb == 'POST'):
			logging.info(f"saving a new audio deliver")
			r = requests.post(word_count_service + deliver_assignment_endpoint, json={
			"assignment_id": assignment_id,
			"student_id": student_id,
			"audio_URL": telegram_audio_endpoint + telegram_token + '/' + file_name,
			"total_words_detected": total_words_detected,
			"speech_to_text": speech_to_text,
			"arrive_at": date
			})
		else:
			logging.info(f"updating a  audio deliver")
			r = requests.put(word_count_service + deliver_assignment_endpoint + "/" + str(deliver_assignment_id), json={
			"assignment_id": assignment_id,
			"student_id": student_id,
			"audio_URL": telegram_audio_endpoint + telegram_token + '/' + file_name,
			"total_words_detected": total_words_detected,
			"speech_to_text": speech_to_text,
			"arrive_at": date
			})
		return r.json()
	except requests.exceptions.RequestException as e:
		logging.warning(f"The deliver was not stored in the server. error: {e}")
		raise Exception('The deliver was not stored in the server.')


def get_assignment_id(student_id):
	try:
		logging.info(f"getting assignment id from student_id {student_id}")
		r = requests.get(word_count_service + get_last_assignment_id + "/" + str(student_id))
		json_response = r.json()
		assignment_id = json_response['assignment_id']
		deliver_assignment_id = json_response['deliver_assignment_id']
		if(deliver_assignment_id is not None):
			return assignment_id, 'PUT', deliver_assignment_id
		return assignment_id, 'POST', None
	except requests.exceptions.RequestException as e:
		logging.warning(f"The deliver was not stored in the server. error: {e}")
		raise Exception('The deliver was not stored in the server.')

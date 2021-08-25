import requests
import os

word_count_service = os.environ.get('WORD_COUNTER_SERVICE', 'http://localhost:5000/api')
deliver_assignment_endpoint = os.environ.get('DELIVER_ASSIGNMENT_ENDPOINT','/deliver-assignments')
telegram_token = os.environ['TELEGRAM_TOKEN']
telegram_audio_endpoint = os.environ.get('TELEGRAM_AUDIO_ENDPOINT','https://api.telegram.org/file/bot')

def save_audio_deliver(assignment_id, student_id, file_name, total_words_detected):
	r = requests.post(word_count_service+deliver_assignment_endpoint, json={
	"assignment_id": assignment_id,
	"student_id": student_id,
	"audio_URL": telegram_audio_endpoint + telegram_token + '/' + file_name,
	"total_words_detected": total_words_detected
	})
	return r.json()

import requests
import os
from dotenv import load_dotenv

load_dotenv()

word_count_service = os.environ.get('WORD_COUNTER_SERVICE', 'http://localhost:5000/api')
student_endpoint = os.environ.get('STUDENT_ENDPOINT','/students')

def subscribe(student_id,username):
    r = requests.post(word_count_service + student_endpoint, json={
    "username": username,
    "student_id": student_id
	})

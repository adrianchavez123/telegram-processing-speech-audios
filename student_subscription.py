import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(filename='/home/ec2-user/auto-subscribe-students/logs/test.log', level = logging.DEBUG,
format='%(asctime)s:%(levelname)s:%(message)s')

word_count_service = os.environ.get('WORD_COUNTER_SERVICE', 'http://localhost:5000/api')
student_endpoint = os.environ.get('STUDENT_ENDPOINT','/students')
join_group_endpoint = os.environ.get('JOIN_GROUP_ENDPOINT','/groups/join')

def subscribe(student_id,username):
    try:
        r = requests.post(word_count_service + student_endpoint, json={
        "username": username,
        "student_id": student_id
    	})
        return r.json()
    except requests.exceptions.RequestException as e:
        logging.warning(f"Subscribing student ({student_id}) failed. error: {e}")
        raise Exception('Subscribing student failed.')

def register(student_id, token):
    try:
        r = requests.get(word_count_service + join_group_endpoint + '/' + str(student_id) + '/' + str(token))
        return r.json()
    except requests.exceptions.RequestException as e:
        logging.warning(f"Joining group ({student_id}) failed. error: {e}")
        raise Exception('Joining group failed.')

def update_student_profile(student_id, id):
    try:
        st = requests.get(word_count_service + student_endpoint + "/" + str(id))
        student =  st.json()
        logging.info(student)
        r = requests.put(word_count_service + student_endpoint + "/" + str(id), json={
        "username": student["username"],
        "student_id": student_id
    	})
        return r.json()
    except requests.exceptions.RequestException as e:
        logging.warning(f"Joining group ({student_id}) failed. error: {e}")
        raise Exception('Joining group failed.')

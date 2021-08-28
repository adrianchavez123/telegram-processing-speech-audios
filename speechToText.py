import speech_recognition as sr
import os, json
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

ibm_speech_to_text_api_key = os.environ['IBM_SPEECH_TO_TEXT_API_KEY']
ibm_speech_to_text_url = os.environ['IBM_SPEECH_TO_TEXT_URL']

class SpeechToText():

    def __init__(self, file_name, method):
        self.file_name = file_name
        self.method = method

    def recognize(self):
        if(self.method == 'google'):
            return self._recognize_google()
        elif(self.method == 'ibm'):
            return self._recognize_ibm()
        raise Exception('Unrecognized method to translate speech to text.')

    def _recognize_google(self):
        r = sr.Recognizer()
        with sr.AudioFile(self.file_name) as source:
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio, language="es-MX")
                # print(text)
                return text
            except sr.UnknownValueError:
                print("Audio Unintelligible")

            except sr.RequestError as e:
                print("cannot obtain results : {0}".format(e))
            except:
                print("error, something when wrong")
            return ''

    def _recognize_ibm(self):
        apiKey = ibm_speech_to_text_api_key
        url = ibm_speech_to_text_url
        authenticator = IAMAuthenticator(apiKey)
        stt = SpeechToTextV1(
            authenticator = authenticator
        )
        stt.set_service_url(url)
        with open(self.file_name,'rb') as f:
            res = stt.recognize(audio=f, content_type='audio/wav', model='es-MX_BroadbandModel',continuous=True)
            if(res.get_status_code() != 200):
                return ''
            text = res.get_result()['results'][0]['alternatives'][0]['transcript']
            # print(text)
            return text

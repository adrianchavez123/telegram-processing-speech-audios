import speech_recognition as sr
import os, json
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from vosk import Model, KaldiRecognizer, SetLogLevel
import wave
from dotenv import load_dotenv
from os import environ, path
from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *
load_dotenv()

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
        elif(self.method == 'vosk'):
            return self._recognize_vosk()
        elif(self.method == 'sphinx'):
            return self._recognize_sphinx()
        raise Exception('Unrecognized method to translate speech to text.')

    def _recognize_sphinx(self):
        config = Decoder.default_config()
        config.set_string('-hmm', 'sphinx/cmusphinx-es-5.2/model_parameters/voxforge_es_sphinx.cd_ptm_4000')
        config.set_string('-lm', 'sphinx/es-20k.lm.gz')
        config.set_string('-dict', 'sphinx/es.dict')

        decoder = Decoder(config)
        decoder.start_utt()
        stream = open(self.file_name, 'rb')
        while True:
          buf = stream.read(1024)
          if buf:
            decoder.process_raw(buf, False, False)
          else:
            break
        decoder.end_utt()
        words = []
        for seg in decoder.seg():
            if "<" not in seg.word:
                words.append(seg.word)
        return ' '.join(words)

    def _recognize_vosk(self):
        SetLogLevel(0)
        if not os.path.exists("vosk-model-small-es-0.3"):
            raise Exception("Please download the model from https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.")
        text = []
        wf = wave.open(self.file_name, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            raise Exception("Audio file must be WAV format mono PCM.")
        model = Model("vosk-model-small-es-0.3")
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)

        try:
            res = json.loads(rec.FinalResult())
            return res['text']
        except Exception as e:
            print(e)
            return ""

    def _recognize_google(self):
        r = sr.Recognizer()
        with sr.AudioFile(self.file_name) as source:
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio, language="es-MX")
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
            try:
                text = res.get_result()['results'][0]['alternatives'][0]['transcript']
            except Exception as e:
                print(e)
                return ""

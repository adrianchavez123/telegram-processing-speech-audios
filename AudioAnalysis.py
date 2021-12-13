import numpy as np
from pydub.utils import make_chunks
from pydub.silence import split_on_silence
from dotenv import load_dotenv
import logging, os, librosa
from speechDetection import SpeechDetection
from speechActivityDetection import SpeechActivityDetection
from audio_helper import recognize, save_segment_of_audios
from audio_io import remove_files

load_dotenv()
log_file = os.environ['LOG_FILE']
logging.basicConfig(filename=log_file, level = logging.INFO,
format='%(asctime)s:%(levelname)s:%(message)s')

class AudioAnalysis():

    def __init__(self, audio_file):
        self.audio_file = audio_file

    def set_sound(self, sound):
        self.sound = sound

    def process(self, method):
        logging.info(f" executing audio analysis, method={method}, file_name={self.audio_file}")
        if(method == 'AMPLITUDE_TO_DB'):
            return self._analyze_by_amplitude_level()
        elif(method == 'ENERGY_AND_TWO_STAGE_WIDE_BAND'):
            return self._analyze_by_energy_and_band_filters()
        elif(method == 'ZERO_CROSSING_RATE'):
            return self._analyze_by_zero_crossing_rate()
        elif(method == 'SHORT_TIME_ENERGY'):
            return self._analyze_by_short_time_energy()
        return self._analyze_split_audio_by_silence()

    def _analyze_by_amplitude_level(self):
        logging.info(f" executing analyze_by_amplitude_level(), file_name={self.audio_file}")

        Signal,sr = librosa.load(self.audio_file)
        #n_fft = 512
        #coeffficients = librosa.stft(Signal,n_fft=n_fft, hop_length=n_fft//4,window=signal.windows.hamming, center=True)
        #db = librosa.amplitude_to_db(np.abs(coeffficients),ref=np.max)


        fragments = librosa.effects.split(Signal, top_db=16) # audio above 16db

        file_names = save_segment_of_audios(Signal, self.audio_file, sr)
        text = recognize(file_names)
        remove_files(file_names)
        return str(len(fragments)), text


    def _analyze_by_energy_and_band_filters(self):
        logging.info(f" executing analyze_by_energy_and_band_filters(), file_name={self.audio_file}")
        detection = SpeechDetection(self.audio_file)
        signal, rate = detection.get_data()
        speech = detection.detect_speech()
        print(f" fragmentos: {str(len(speech))}")
        file_names = save_segment_of_audios(signal, self.audio_file, rate)
        text = recognize(file_names)
        remove_files(file_names)
        return str(len(speech)), text

    def _analyze_by_short_time_energy(self):
        logging.info(f" executing _analyze_by_short_time_energy(), file_name={self.audio_file}")
        detection = SpeechActivityDetection(self.audio_file)
        signal, rate = detection.get_data()
        speech = detection.detect_speech()
        print(f" fragmentos: {str(len(speech))}")
        file_names = save_segment_of_audios(signal, self.audio_file, rate)
        text = recognize(file_names)
        remove_files(file_names)
        return str(len(speech)), text

    def _analyze_split_audio_by_silence(self):
        logging.info(f" executing analyze_split_audio_by_silence(), file_name={self.audio_file}")
        audio_chunks = split_on_silence(self.sound,
            min_silence_len=100,
            silence_thresh=-35,
            keep_silence=60,
            seek_step=1
        )
        # when the signal is reconstructed, the sound is chopping
        #chunk_file_names = save_chunks_of_audios(audio_chunks, file_name)
        #text = recognize(chunk_file_names)
        #return str(len(audio_chunks)), text

        # better option to construct audio segments
        Signal,sr = librosa.load(self.audio_file)
        file_names = save_segment_of_audios(Signal, self.audio_file, sr)
        text = recognize(file_names)
        remove_files(file_names)
        return str(len(audio_chunks)), text

    def _analyze_by_zero_crossing_rate(self):
        logging.info(f" executing analyze_split_audio_by_zero_crossing_rate(), file_name={self.audio_file}")
        chunk_length_ms = 400 # in millisec
        chunks = make_chunks(self.sound, chunk_length_ms) #Make chunks
        audio_chunks_total = []
        for i, chunk in enumerate(chunks):
            samples = chunk[i].get_array_of_samples()
            audioData = np.array(samples)
            suma =  ((audioData[:-1] * audioData[1:]) < 0).sum()
            if(suma > 20):
                audio_chunks_total.append(suma)

        # better option to construct audio segments
        Signal,sr = librosa.load(self.audio_file)
        file_names = save_segment_of_audios(Signal, self.audio_file, sr)
        text = recognize(file_names)
        remove_files(file_names)
        return str(len(audio_chunks_total)), text

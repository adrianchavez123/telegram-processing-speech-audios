import numpy as np
import scipy
import scipy.signal
import scipy.io.wavfile as wf


class SpeechActivityDetection():

    def __init__(self, wave_input_filename):
        self.rate, self.data = wf.read(wave_input_filename)

    def get_audio(self):
        return self.data

    def get_rate(self):
        return self.rate

    def get_data(self):
        return self.data, self.rate

    def get_energy(self):
        return self.energy

    def get_vad(self):
        return self.vad

    def get_voice(self):
        return self.voice

    def detect_speech(self):
        energy, vad, voice = self.calculate_energy_and_split_voice_and_no_voice()
        self.energy = energy
        self.vad = vad
        self.voice = voice
        voice_peaks,_ = scipy.signal.find_peaks(voice, distance=20000)
        return voice_peaks

    def _stride_trick(self, data, stride_length, stride_step):
        nrows = ((data.size - stride_length) // stride_step) + 1
        n = data.strides[0]
        return np.lib.stride_tricks.as_strided(data,
                                               shape=(nrows, stride_length),
                                               strides=(stride_step*n, n))

    def _get_frames(self, window_len=0.05, window_hop=0.05):

        if window_len < window_hop: raise Exception('Window hop can not be bigger that window length.')

        # seconds to frames
        frame_length = window_len * self.rate
        frame_step = window_hop * self.rate
        signal_length = len(self.data)
        frames_overlap = frame_length - frame_step

        rest_samples = np.abs(signal_length - frames_overlap) % np.abs(frame_length - frames_overlap)
        pad_signal = np.append(self.data, np.array([0] * int(frame_step - rest_samples) * int(rest_samples != 0.)))
        frames = self._stride_trick(pad_signal, int(frame_length), int(frame_step))
        return frames, frame_length

    def short_time_energy(self, frames):
        return np.sum(np.abs(np.fft.rfft(a=frames, n=len(frames)))**2, axis=-1) / len(frames)**2

    def calculate_energy_and_split_voice_and_no_voice(self, threshold=-20, window_len=0.05, window_hop=0.05, E0=1e7):
        frames, frames_len = self._get_frames(window_len=window_len, window_hop=window_hop)
        energy = self.short_time_energy(frames)

        log_energy = 10 * np.log10(energy / E0)

        # normalize
        energy = scipy.signal.medfilt(log_energy, 5)
        energy[energy <= -1E20] = 0 # avoid - Inf numbers
        energy = np.repeat(energy, frames_len)

        threshold = np.mean(energy) # dynamic threshold, voice levels vary from audio file
        #threshold = np.mean(energy) + np.mean(energy)* 0.10

        voice_activity_detection     = np.array(energy > threshold, dtype=self.data.dtype)
        vframes = np.array(frames.flatten()[np.where(voice_activity_detection==1)], dtype=self.data.dtype)
        return energy, voice_activity_detection, np.array(vframes, dtype=np.float64)

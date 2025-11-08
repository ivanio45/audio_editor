import struct

from editor.mp3Decoder.util import get_mp3_audio_start_offset
from editor.mp3Decoder.Frame import *


class Decoder:
    """
    Класс для создания wav-файла из mp3-файла.
    """

    def __init__(self, file_path, output_file_path):
        with open(file_path, 'rb') as f:
            self.__file_data = [c for c in f.read()]
        self.__offset = get_mp3_audio_start_offset(self.__file_data[:20])
        self.__buffer = self.__file_data[self.__offset:]

        self.__curr_frame = Frame()
        self.__pcm_data = np.array([])
        self.__file_length = len(self.__file_data)
        self.__wav_file_path = output_file_path

    def __init_curr_header(self):
        if self.__buffer[0] == 0xFF and self.__buffer[1] >= 0xE0:
            self.__curr_frame.init_header_params(self.__buffer)

    def __init_curr_frame(self):
        self.__curr_frame.init_frame_params(
            self.__buffer, self.__file_data, self.__offset)

    def parse_file(self):
        """
        декодирование mp3, кадр за кадром
        и сохранение окончательных данных PCM.
        """
        pcm_data = []

        while self.__file_length > self.__offset + 4:
            self.__init_curr_header()
            self.__init_curr_frame()

            self.__offset += self.__curr_frame.frame_size
            self.__buffer = self.__file_data[self.__offset:]

            pcm_data.extend(list(self.__curr_frame.pcm.copy()))

        self.__pcm_data = np.array(pcm_data)

    def write_to_wav(self):
        """
        Конвертировать PCM в WAV и записать в файл.
        """
        sample_rate = self.__curr_frame.sampling_rate
        num_channels = 1 \
            if len(self.__pcm_data.shape) == 1 else self.__pcm_data.shape[1]
        num_samples = len(self.__pcm_data)
        bytes_per_sample = 2
        byte_rate = sample_rate * num_channels * bytes_per_sample
        block_align = num_channels * bytes_per_sample

        with open(self.__wav_file_path, 'wb') as wav_file:
            wav_file.write(struct.pack('<4s', b'RIFF'))
            wav_file.write(struct.pack(
                '<I', 36 + num_samples * num_channels * bytes_per_sample))
            wav_file.write(struct.pack('<4s', b'WAVE'))

            wav_file.write(struct.pack('<4s', b'fmt '))
            wav_file.write(struct.pack('<I', 16))
            wav_file.write(struct.pack('<H', 1))
            wav_file.write(struct.pack('<H', num_channels))
            wav_file.write(struct.pack('<I', sample_rate))
            wav_file.write(struct.pack('<I', byte_rate))
            wav_file.write(struct.pack('<H', block_align))
            wav_file.write(struct.pack('<H', bytes_per_sample * 8))

            wav_file.write(struct.pack('<4s', b'data'))
            wav_file.write(struct.pack(
                '<I', num_samples * num_channels * bytes_per_sample))

            pcm_16bit = (self.__pcm_data * 32767).astype(np.int16)
            wav_file.write(pcm_16bit.tobytes())

    def decode(self):
        """
        Декодирование входного файла mp3 в файл wav.
        """
        self.parse_file()
        self.write_to_wav()

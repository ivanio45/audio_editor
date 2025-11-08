from enum import Enum
from editor.mp3Decoder.tables import *
import numpy as np


class Band:
    """
    Класс Band используется для
    хранения массивов индексов и ширин полос частот,
    которые зависят от частоты
    дискретизации и типа окна (длинное или короткое).
    """

    def __init__(self):
        self.long_win = []
        self.short_win = []


class ChannelMode(Enum):
    """
    Режимы каналов, используемые в MP3.
    """
    Stereo = 0
    JointStereo = 1
    DualChannel = 2
    Mono = 3


class FrameHeader:
    """
    Класс заголовка кадра содержит
    всю информацию текущего заголовка кадра в mp3-файле.
    """
    MPEG1_SAMPLING_RATES = [44100, 48000, 32000]
    MPEG1_LAYER3_BITRATES = \
        [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]

    def __init__(self):
        self.buffer = []
        self.mpeg_version = 1
        self.layer = 3
        self.crc = False
        self.bit_rate = 0
        self.sampling_rate = 0
        self.padding = False
        self.channel_mode = ChannelMode(0)
        self.channels = 0
        self.mode_extension = [0, 0]
        self.band_index = Band()
        self.band_width = Band()

    def init_header_params(self, buffer):
        """
        Распаковывает заголовок MP3-фрейма.

        :param buffer: буфер, содержащий
        байты MP3-файла, начиная с первых байтов заголовка.
        """
        self.buffer = buffer
        self.crc = bool(self.buffer[1] & 0x01)
        sampling_bits = (self.buffer[2] & 0x0C) >> 2
        self.sampling_rate = self.MPEG1_SAMPLING_RATES[sampling_bits]

        self.__set_tables()

        channel_mode_value = (self.buffer[3] >> 6)
        self.channel_mode = ChannelMode(channel_mode_value)
        self.channels = 1 \
            if self.channel_mode == ChannelMode.Mono else 2

        self.mode_extension = \
            [(self.buffer[3] & 0x20) >> 5, (self.buffer[3] & 0x10) >> 4]

        self.padding = bool(self.buffer[2] & 0x02)

        bitrate_bits = (self.buffer[2] & 0xF0) >> 4
        if 0 < bitrate_bits < len(self.MPEG1_LAYER3_BITRATES):
            self.bit_rate = self.MPEG1_LAYER3_BITRATES[bitrate_bits] * 1000
        elif bitrate_bits == 0:
            self.__valid = False

    def __set_tables(self):
        """
        Во время процесса декодирования
        используются различные таблицы
        в зависимости от частоты дискретизации.
        """
        if self.sampling_rate == 32000:
            self.band_index.short_win = np.array(band_index_table.short_32)
            self.band_width.short_win = np.array(band_width_table.short_32)
            self.band_index.long_win = np.array(band_index_table.long_32)
            self.band_width.long_win = np.array(band_width_table.long_32)
        elif self.sampling_rate == 44100:
            self.band_index.short_win = np.array(band_index_table.short_44)
            self.band_width.short_win = np.array(band_width_table.short_44)
            self.band_index.long_win = np.array(band_index_table.long_44)
            self.band_width.long_win = np.array(band_width_table.long_44)
        elif self.sampling_rate == 48000:
            self.band_index.short_win = np.array(band_index_table.short_48)
            self.band_width.short_win = np.array(band_width_table.short_48)
            self.band_index.long_win = np.array(band_index_table.long_48)
            self.band_width.long_win = np.array(band_width_table.short_48)

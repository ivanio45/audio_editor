from editor.mp3Decoder.FrameHeader import *
from editor.mp3Decoder.util import *
import numpy as np


class FrameSideInformation:
    """
    Класс, представляющий
    информацию (side information) MP3-фрейма.
    Side information содержит
    информацию, необходимую для
    декодирования основных данных (main data).
    """

    def __init__(self):
        self.main_data_begin = 0
        self.scfsi: np.ndarray = np.zeros((2, 4))

        self.part2_3_length: np.ndarray = np.zeros((2, 2))
        self.part2_length: np.ndarray = np.zeros((2, 2))
        self.big_value: np.ndarray = np.zeros((2, 2))
        self.global_gain: np.ndarray = np.zeros((2, 2))
        self.scale_fac_compress: np.ndarray = np.zeros((2, 2))
        self.slen1: np.ndarray = np.zeros((2, 2))
        self.slen2: np.ndarray = np.zeros((2, 2))
        self.window_switching: np.ndarray = np.zeros((2, 2))
        self.block_type: np.ndarray = np.zeros((2, 2))
        self.mixed_block_flag: np.ndarray = np.zeros((2, 2))
        self.switch_point_l: np.ndarray = np.zeros((2, 2))
        self.switch_point_s: np.ndarray = np.zeros((2, 2))
        self.table_select: np.ndarray = np.zeros((2, 2, 3))
        self.sub_block_gain: np.ndarray = np.zeros((2, 2, 3))
        self.region0_count: np.ndarray = np.zeros((2, 2))
        self.region1_count: np.ndarray = np.zeros((2, 2))
        self.pre_flag: np.ndarray = np.zeros((2, 2))
        self.scale_fac_scale: np.ndarray = np.zeros((2, 2))
        self.count1table_select: np.ndarray = np.zeros((2, 2))

        self.scale_fac_l: np.ndarray = np.zeros((2, 2, 22))
        self.scale_fac_s: np.ndarray = np.zeros((2, 2, 3, 13))

    def set_side_info(self, buffer, header):
        """
        Side information содержит
        информацию о том, как декодировать main_data.
        """

        offset = 0

        # Получить указатель начала main data из буфера
        self.main_data_begin = get_bits(buffer, 0, 9)
        offset += 9
        # Пропустить приватные биты
        offset += 5 if header.channel_mode == ChannelMode.Mono else 3

        for ch in range(header.channels):
            for scfsi_band in range(4):
                self.scfsi[ch][scfsi_band] = get_bits(buffer, offset, 1) != 0
                offset += 1

        for gr in range(2):
            for ch in range(header.channels):
                # Длина масштабных коэффициентов и main data в битах.
                self.part2_3_length[gr][ch] = get_bits(buffer, offset, 12)
                offset += 12
                self.big_value[gr][ch] = get_bits(buffer, offset, 9)
                offset += 9
                self.global_gain[gr][ch] = get_bits(buffer, offset, 8)
                offset += 8
                self.scale_fac_compress[gr][ch] = get_bits(buffer, offset, 4)
                offset += 4
                self.slen1[gr][ch] = (
                    slen)[int(self.scale_fac_compress[gr][ch])][0]
                self.slen2[gr][ch] = (
                    slen)[int(self.scale_fac_compress[gr][ch])][1]
                self.window_switching[gr][ch] = (
                        get_bits(buffer, offset, 1) == 1)
                offset += 1

                if self.window_switching[gr][ch]:
                    self.block_type[gr][ch] = get_bits(buffer, offset, 2)
                    offset += 2
                    self.mixed_block_flag[gr][ch] = (
                            get_bits(buffer, offset, 1) == 1)
                    offset += 1
                    if self.mixed_block_flag[gr][ch]:
                        self.switch_point_l[gr][ch] = 8
                        self.switch_point_s[gr][ch] = 3

                    self.region0_count[gr][ch] = \
                        8 if self.block_type[gr][ch] == 2 else 7
                    # Третьего региона нет
                    self.region1_count[gr][ch] = (
                            20 - self.region0_count[gr][ch])

                    for region in range(2):
                        # Номер таблицы Хаффмана для большого региона
                        self.table_select[gr][ch][region] = (
                            get_bits(buffer, offset, 5))
                        offset += 5
                    for window in range(3):
                        self.sub_block_gain[gr][ch][window] = (
                            get_bits(buffer, offset, 3))
                        offset += 3

                else:
                    self.block_type[gr][ch] = 0
                    self.mixed_block_flag[gr][ch] = False

                    for region in range(3):
                        self.table_select[gr][ch][region] = (
                            get_bits(buffer, offset, 5))
                        offset += 5

                    self.region0_count[gr][ch] = (
                        get_bits(buffer, offset, 4))
                    offset += 4
                    self.region1_count[gr][ch] =\
                        get_bits(buffer, offset, 3)
                    offset += 3

                self.pre_flag[gr][ch] = get_bits(buffer, offset, 1)
                offset += 1
                # Определяет размер шага.
                self.scale_fac_scale[gr][ch] = get_bits(buffer, offset, 1)
                offset += 1
                # Таблица, определяющая, какая таблица count1 используется.
                self.count1table_select[gr][ch] = get_bits(buffer, offset, 1)
                offset += 1

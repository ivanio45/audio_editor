import math
from tkinter import messagebox

from editor.mp3Decoder.decoder import Decoder
from editor.wav_parser import WavParser
from history_manager import HistoryManager


def _get_sample_value(byte_data, sample_index, sample_width):
    """
    Возвращает целочисленное значение сэмпла
    по его индексу. 0, если индекс вне диапазона.
    """
    total_samples = len(byte_data) // sample_width
    if 0 <= sample_index < total_samples:
        byte_index = sample_index * sample_width
        if byte_index + sample_width <= len(byte_data):
            return int.from_bytes(
                byte_data[byte_index: byte_index + sample_width],
                byteorder='little', signed=True)
    return 0


class AudioEditor:
    def __init__(self, file_path):
        """
        Инициализация
        """
        self.file_path = file_path
        if self.file_path.lower().endswith(".mp3"):
            # Если файл является MP3, декодируем его во временный WAV-файл
            temp_wav_path = self.file_path[:-4] + "_temp.wav"
            mp3_converter = Decoder(self.file_path, temp_wav_path)
            mp3_converter.decode()
            self.file_path = temp_wav_path
        self.output_path = None
        self.audio_data = WavParser(self.file_path)
        self.seconds = (self.audio_data.getnframes() /
                        self.audio_data.getframerate())
        self.history_manager = HistoryManager(self.file_path)
        self._temp_file_counter = 0

    def get_audio_seconds(self):
        """
        Вычисляет и возвращает длительность аудиофайла в секундах.
        """
        return self.audio_data.getnframes() / self.audio_data.getframerate()

    def change_speed(self, speed_factor, need_save=True):
        """
        Изменяет скорость воспроизведения аудио.
        """
        params = self.audio_data.getparams()
        sampwidth = params[1]
        frames = self.audio_data.frames

        if speed_factor > 1:
            frames = self._speed_up(frames, sampwidth, speed_factor)
        if speed_factor < 1:
            frames = self._interpolate(frames, sampwidth, speed_factor)

        if need_save:
            self._save_audio(frames, params)
        else:
            print("ya tut")
            return frames

        messagebox.showinfo("Готово", "Вы изменили скорость аудио.")

    def _speed_up(self, frames, sampwidth, speed_factor):
        """
        Ускоряет аудиоданные путем удаления кадров.
        """
        num_original_samples = len(frames) // sampwidth
        new_audio_data = bytearray()
        original_sample_index = 0.0
        for i in range(int(num_original_samples / speed_factor)):
            index_to_take = int(original_sample_index)
            start_byte = index_to_take * sampwidth
            end_byte = start_byte + sampwidth
            if end_byte <= len(frames):
                new_audio_data.extend(frames[start_byte:end_byte])
            original_sample_index += speed_factor
        return new_audio_data

    def _interpolate(self, frames, sampwidth, speed_factor):
        """
        Замедляет аудиоданные путем интерполяции новых сэмплов.
        """
        factor = 1 / speed_factor
        new_audio_data = bytearray()
        if factor >= 2:
            for i in range(0, len(frames), sampwidth):
                current_sample = frames[i:i + sampwidth]
                new_audio_data.extend(current_sample)
                num_interp_samples = int(factor) - 1
                for j in range(num_interp_samples):
                    interpolated_sample = self._interpolation(
                        frames, i, sampwidth, j / (num_interp_samples + 1))
                    new_audio_data.extend(interpolated_sample)
        else:
            number_of_sample = 0
            count = int(1 / (1 - speed_factor))
            for i in range(0, len(frames), sampwidth):
                current_sample = frames[i:i + sampwidth]
                new_audio_data.extend(current_sample)
                if number_of_sample == count:
                    interpolated_sample = self._interpolation(
                        frames, i, sampwidth, 0.5)
                    new_audio_data.extend(interpolated_sample)
                    number_of_sample = 0
                else:
                    number_of_sample += 1

        return new_audio_data

    def _interpolation(self, audio_data, start_index, sample_width, factor):
        """
        Выполняет линейную интерполяцию между двумя аудиосэмплами.
        """
        start_sample = int.from_bytes(
            audio_data[start_index:start_index + sample_width],
            byteorder='little',
            signed=True)
        next_sample_index = start_index + sample_width
        next_sample = int.from_bytes(
            audio_data[next_sample_index:next_sample_index + sample_width],
            byteorder='little',
            signed=True)
        interpolated_value = (start_sample +
                              (next_sample - start_sample) * factor)
        return int(interpolated_value).to_bytes(
            sample_width,
            byteorder='little',
            signed=True)

    def cut(self, start_time, end_time):
        """
        Обрезает часть аудиофайла между указанным временем начала и окончания.
        """
        rate = self.audio_data.getframerate()
        start_frame = int(start_time * rate)
        end_frame = int(end_time * rate)
        params = self.audio_data.getparams()
        start_byte = start_frame * params[1] * params[0]
        end_byte = end_frame * params[1] * params[0]
        frames = self.audio_data.frames[start_byte:end_byte]
        self._save_audio(frames, params)
        messagebox.showinfo("Готово", "Вы обрезали аудио.")

    def combine(self, second_file_path):
        """
        Объединяет текущий аудиофайл с другим аудиофайлом.
        """
        params1 = self.audio_data.getparams()
        frames1 = self.audio_data.frames
        if second_file_path.lower().endswith(".mp3"):
            # Если файл является MP3, декодируем его во временный WAV-файл
            temp_wav_path = second_file_path[:-4] + "_temp.wav"
            mp3_converter = Decoder(second_file_path, temp_wav_path)
            mp3_converter.decode()
            second_file_path = temp_wav_path
        parser2 = WavParser(second_file_path)
        frames2 = parser2.frames
        frames = frames1 + frames2
        self._save_audio(frames, params1)
        messagebox.showinfo("Готово", f"Аудио склеены.")

    def export(self, output_path):
        """
        Экспортирует текущее состояние аудио в новый файл.
        """
        params = self.audio_data.getparams()
        frames = self.audio_data.frames
        try:
            WavParser(self.file_path).write_wav(output_path, params, frames)
        except IOError as e:
            messagebox.showerror("Ошибка",
                                 f"Ошибка ввода/вывода при записи файла: {e}")
            return
        messagebox.showinfo("Готово", f"Аудио сохранено в {output_path}")

    def _create_temp_file_path(self):
        """
        Создает путь для временного файла.
        """
        self._temp_file_counter += 1
        return f"_temp/temp_audio_{self._temp_file_counter}.wav"

    def _save_audio(self, frames, params, out_path=None):
        """
        Сохраняет измененные аудиоданные во
        временный файл и обновляет текущий путь к файлу.
        """
        if out_path is None:
            out_path = self._create_temp_file_path()

        WavParser(self.file_path).write_wav(out_path, params, frames)
        self.file_path = out_path
        self.audio_data = WavParser(out_path)
        self.seconds = self.get_audio_seconds()
        self.history_manager.add_state(self.file_path)

    def apply_reverb(self, first_delay_seconds, first_decay_factor):
        """
        Применяет эффект реверберации.
        """
        if first_delay_seconds <= 0:
            messagebox.showerror("Ошибка",
                                 "Задержка должна быть больше 0.")
            return
        if first_decay_factor < 0 or first_decay_factor > 1:
            messagebox.showerror("Ошибка",
                                 "Фактор затухания должен быть от 0 до 1.")
            return

        second_delay_seconds = first_delay_seconds * 1.5
        second_decay_factor = first_decay_factor * 0.6

        third_delay_seconds = first_delay_seconds * 2.2
        third_decay_factor = first_decay_factor * 0.3

        taps_params = [
            (first_delay_seconds, first_decay_factor),
            (second_delay_seconds, second_decay_factor),
            (third_delay_seconds, third_decay_factor),
        ]

        params = self.audio_data.getparams()
        num_channels = params[0]
        sample_width = params[1]
        framerate = params[2]
        original_frames_bytes = self.audio_data.frames
        original_total_samples = len(original_frames_bytes) // sample_width

        max_val = 2 ** (8 * sample_width - 1) - 1
        min_val = - (2 ** (8 * sample_width - 1))

        delay_samples_list = []
        max_delay_samples = 0
        for delay_sec, _ in taps_params:
            delay_s = int(delay_sec * framerate * num_channels)
            delay_samples_list.append(delay_s)
            if delay_s > max_delay_samples:
                max_delay_samples = delay_s

        processed_frames = bytearray()
        total_output_samples = original_total_samples + max_delay_samples

        for i in range(total_output_samples):
            orig_sample_value = _get_sample_value(
                original_frames_bytes, i, sample_width)

            processed_value = orig_sample_value

            for j in range(len(taps_params)):
                delay_s = delay_samples_list[j]  # Задержка  в сэмплах
                decay_f = taps_params[j][1]  # Фактор затухания

                delayed_sample_value = _get_sample_value(
                    original_frames_bytes, i - delay_s, sample_width)

                processed_value += int(delayed_sample_value * decay_f)

            processed_value = max(min(processed_value, max_val), min_val)

            processed_frames.extend(processed_value.to_bytes(
                sample_width, byteorder='little', signed=True))
        self._save_audio(processed_frames, params)

        messagebox.showinfo("Готово", "Реверберация применена.")

    def hann_window(self, size):
        """
        Генерирует оконную функцию Ханна.
        Применяется к сегментам аудио для
        сглаживания краев и уменьшения артефактов.
        """
        if size <= 0:
            return []
        if size == 1:
            return [1.0]
        # Формула окна Ханна
        return [0.5 * (1.0 - math.cos(2.0 * math.pi * i /
                                      (size - 1.0))) for i in range(size)]

    def _resample_segment_for_pitch_samples(
            self, segment_samples, pitch_factor):
        """
        Ресамплирует сегмент.
        """
        original_len_samples = len(segment_samples)
        if original_len_samples == 0 or pitch_factor <= 0:
            return []

        target_len_samples = int(original_len_samples / pitch_factor)

        if target_len_samples == 0:
            return []

        new_segment_samples = []

        for i in range(target_len_samples):
            current_read_pos = i * pitch_factor
            p1_idx = int(current_read_pos)
            p0_idx = p1_idx - 1
            p2_idx = p1_idx + 1
            p3_idx = p1_idx + 2

            interp_factor = current_read_pos - p1_idx

            p0 = segment_samples[p0_idx] \
                if 0 <= p0_idx < original_len_samples else 0.0
            p1 = segment_samples[p1_idx] \
                if 0 <= p1_idx < original_len_samples else 0.0
            p2 = segment_samples[p2_idx] \
                if 0 <= p2_idx < original_len_samples else 0.0
            p3 = segment_samples[p3_idx] \
                if 0 <= p3_idx < original_len_samples else 0.0

            f = interp_factor
            a0 = p3 - p2 - p0 + p1
            a1 = p0 - p1 - a0
            a2 = p2 - p0
            a3 = p1

            interpolated_value = a0 * f * f * f + a1 * f * f + a2 * f + a3
            new_segment_samples.append(interpolated_value)
        return new_segment_samples

    def apply_ola_pitch_shift(
            self, pitch_factor, window_size_ms=120, hop_size_ms=30):
        """
        Применяет Pitch Shift без изменения
        длительности, используя простой Overlap-Add.
        """
        params = self.audio_data.getparams()
        sample_width = params[1]
        framerate = params[2]
        original_frames_bytes = self.audio_data.frames
        original_total_samples = len(original_frames_bytes) // sample_width
        window_size_samples = int(window_size_ms * framerate / 1000.0)
        hop_size_samples = int(hop_size_ms * framerate / 1000.0)
        if window_size_samples <= 0:
            messagebox.showerror("Ошибка",
                                 "Размер окна в сэмплах получился <= 0.")
            return
        if hop_size_samples <= 0:
            messagebox.showerror("Ошибка",
                                 "Размер хопа в сэмплах получился <= 0.")
            return
        window = self.hann_window(window_size_samples)

        output_buffer_size = original_total_samples + window_size_samples * 2
        output_buffer = [0.0] * output_buffer_size

        # --- Основной цикл Overlap-Add ---
        input_sample_pointer = 0
        output_sample_pointer = 0

        while input_sample_pointer < original_total_samples:
            segment_start_sample_idx = input_sample_pointer
            segment_end_sample_idx = min(
                input_sample_pointer +
                window_size_samples,
                original_total_samples)
            current_segment_samples_int = []

            for i in range(segment_start_sample_idx, segment_end_sample_idx):
                current_segment_samples_int.append(
                    _get_sample_value(
                        original_frames_bytes,
                        i, sample_width))

            current_segment_samples_float = \
                [float(s) for s in current_segment_samples_int]
            if len(current_segment_samples_float) < window_size_samples:
                current_segment_samples_float.extend(
                    [0.0] * (window_size_samples -
                             len(current_segment_samples_float)))

            windowed_segment_samples = \
                [current_segment_samples_float[i] * window[i]
                 for i in range(window_size_samples)]

            processed_segment_samples = (
                self._resample_segment_for_pitch_samples(
                    windowed_segment_samples, pitch_factor))
            current_output_offset = output_sample_pointer
            for i in range(len(processed_segment_samples)):
                output_index = current_output_offset + i
                if output_index < len(output_buffer):
                    output_buffer[output_index] += (
                        processed_segment_samples)[i]

            input_sample_pointer += hop_size_samples
            output_sample_pointer += hop_size_samples

        final_processed_frames = bytearray()

        max_val = (2 ** (sample_width * 8 - 1)) - 1
        min_val = -(2 ** (sample_width * 8 - 1))
        samples_to_convert = original_total_samples

        for i in range(samples_to_convert):
            sample_value_float = output_buffer[i]
            clamped_value_int = max(
                min_val, min(max_val, int(sample_value_float)))
            final_processed_frames.extend(
                clamped_value_int.to_bytes(
                    sample_width, byteorder='little', signed=True))

        self._save_audio(final_processed_frames, params)
        messagebox.showinfo("Готово", "Изменение тона применено.")

    def undo(self):
        previous_state = self.history_manager.get_previous_state()
        if previous_state:
            self.file_path = previous_state
            self.audio_data = WavParser(self.file_path)
            self.seconds = self.get_audio_seconds()
            messagebox.showinfo("Готово", "Изменение отменено.")

    def redo(self):
        next_state = self.history_manager.get_next_state()
        if next_state:
            self.file_path = next_state
            self.audio_data = WavParser(self.file_path)
            self.seconds = self.get_audio_seconds()
            messagebox.showinfo("Готово", "Изменение применено.")

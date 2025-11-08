import os
import tkinter as tk
from tkinter import filedialog, messagebox
import pygame
import threading
import time
from audio_editor import AudioEditor


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Editor")
        self.root.geometry("950x400")
        self.audio_editor = None
        self.is_playing = False
        pygame.mixer.init()

        self.menubar = tk.Menu(root)
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="Загрузить", command=self.load)
        file_menu.add_command(label="Сохранить как", command=self.export)
        file_menu.add_command(
            label="Загрузить скрипт...", command=self.load_script)
        self.menubar.add_cascade(label="Файл", menu=file_menu)
        self.menubar.add_cascade(
            label="Назад", command=self.undo, state=tk.DISABLED)
        self.menubar.add_cascade(
            label="Вперед", command=self.redo, state=tk.DISABLED)
        root.config(menu=self.menubar, bg="lightblue")

        top_button_frame = tk.Frame(root, bg="lightblue")
        top_button_frame.grid(
            row=0, column=0, columnspan=3, pady=10, sticky="ew")

        default_font = ("Arial", 14)

        self.speed_factor_button = tk.Button(
            top_button_frame, text="Изменить скорость", command=self.speed,
            state=tk.DISABLED,
            font=default_font, width=15, height=2, fg="black", bg="#A6BDD7")
        self.speed_factor_button.grid(row=0, column=0, padx=10)
        self.start_time_label = tk.Label(
            top_button_frame, text="Множитель x:")
        self.start_time_label.grid(row=1, column=0, padx=5)

        self.speed_factor = tk.Entry(top_button_frame, width=10)
        self.speed_factor.grid(row=2, column=0, padx=5)

        self.cut_button = tk.Button(
            top_button_frame,
            text="Обрезать", command=self.cut, state=tk.DISABLED,
            font=default_font, width=15, height=2, fg="black", bg="#A6BDD7")
        self.cut_button.grid(row=0, column=1, padx=5)

        self.start_time_label = tk.Label(
            top_button_frame, text="Начало (сек):")
        self.start_time_label.grid(row=1, column=1, padx=5)
        self.start_time_entry = tk.Entry(
            top_button_frame, width=10)
        self.start_time_entry.grid(row=2, column=1, padx=5)

        self.end_time_label = tk.Label(
            top_button_frame, text="Конец (сек):")
        self.end_time_label.grid(row=3, column=1, padx=5)
        self.end_time_entry = tk.Entry(top_button_frame, width=10)
        self.end_time_entry.grid(row=4, column=1, padx=5)

        self.combine_button = tk.Button(
            top_button_frame, text="Склеить",
            command=self.combine_audio, state=tk.DISABLED,
            font=default_font, width=15, height=2, fg="black", bg="#A6BDD7")
        self.combine_button.grid(row=0, column=2, padx=5)

        self.reverb_button = tk.Button(
            top_button_frame,
            text="Реверберация",
            command=self.apply_reverb_gui,
            state=tk.DISABLED,
            font=default_font, width=15, height=2, fg="black", bg="#A6BDD7")
        self.reverb_button.grid(row=0, column=3, padx=10)

        tk.Label(top_button_frame, text="Задержка (сек):").grid(
            row=1, column=3, padx=5)
        self.reverb_delay_entry = tk.Entry(top_button_frame, width=10)
        self.reverb_delay_entry.grid(row=2, column=3, padx=5)

        tk.Label(top_button_frame, text="Затухание (0-1):").grid(
            row=3, column=3, padx=5)
        self.reverb_decay_entry = tk.Entry(top_button_frame, width=10)
        self.reverb_decay_entry.grid(row=4, column=3, padx=5)

        self.pitch_shift_button = tk.Button(
            top_button_frame,
            text="Изменить Тон",
            command=self.apply_pitch_shift_gui,
            state=tk.DISABLED,
            font=default_font, width=15, height=2, fg="black",
            bg="#A6BDD7")
        self.pitch_shift_button.grid(row=0, column=4, padx=10)

        tk.Label(top_button_frame, text="Фактор:", bg="lightblue").grid(
            row=1, column=4, padx=5)
        self.pitch_factor_entry = tk.Entry(top_button_frame, width=10)
        self.pitch_factor_entry.grid(row=2, column=4, padx=5)

        self.track_name_label = tk.Label(
            root,
            text="Название трека: не загружено",
            font=("Arial", 12),
            bg="lightblue"
        )
        self.track_name_label.grid(
            row=1, column=0, columnspan=3, pady=(0, 5), sticky="ew")

        self.time_slider = tk.Scale(
            root, from_=0, to=100, orient="horizontal",
            command=self.update_time)
        self.time_slider.grid(
            row=2, column=0, columnspan=3, pady=10, sticky="ew")

        button_frame2 = tk.Frame(root)
        button_frame2.grid(row=3, column=0, columnspan=3, pady=10)

        self.play_button = tk.Button(
            button_frame2, text="▶",
            command=self.play, state=tk.DISABLED,
            font=default_font,
            width=15, height=2, fg="black", bg="#A6BDD7")
        self.play_button.grid(row=0, column=0, padx=5)

        self.stop_button = tk.Button(
            button_frame2, text="⏹",
            command=self.stop,
            state=tk.DISABLED,
            font=default_font,
            width=15, height=2, fg="black", bg="#A6BDD7")
        self.stop_button.grid(row=0, column=1, padx=5)

        self.last_action_label = tk.Label(
            root,
            text="Последнее действие: нет изменений",
            font=("Arial", 10),
            bg="lightblue",
            anchor="w"
        )
        self.last_action_label.grid(
            row=4, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

    def load(self):
        file_path = tk.filedialog.askopenfilename(filetypes=[
            ("MP3 Audio Files", "*.mp3"),
            ("WAV Audio Files", "*.wav")])
        if file_path:
            self.audio_editor = AudioEditor(file_path)
            self.speed_factor_button.config(state=tk.NORMAL)
            self.cut_button.config(state=tk.NORMAL)
            self.combine_button.config(state=tk.NORMAL)
            self.play_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            self.menubar.entryconfig("Назад", state=tk.NORMAL)
            self.menubar.entryconfig("Вперед", state=tk.NORMAL)
            self.time_slider.config(to=self.audio_editor.seconds)
            self.reverb_button.config(state=tk.NORMAL)
            self.pitch_shift_button.config(state=tk.NORMAL)
            file_name = os.path.basename(file_path)
            self.track_name_label.config(text=f"Название трека: {file_name}")
            self.update_last_action(f"Загружен файл: {file_name}")

    def load_script(self, file_path=None):
        """
        Открывает диалог выбора файла скрипта и запускает его выполнение.
        """
        if file_path is None:
            file_path = filedialog.askopenfilename(
                defaultextension=".txt",
            )
            if self.audio_editor is None:
                messagebox.showwarning(
                    "Внимание", "Сначала загрузите аудиофайл.")
                return
        self.apply_script(file_path)
        self.update_last_action(f"Загружен скрипт: {os.path.basename(file_path)}")

    def apply_script(self, file_path):
        """
        Читает команды из файла скрипта и выполняет их последовательно.
        """
        try:
            with open(file_path, 'r') as f:
                commands = f.readlines()
            messagebox.showinfo("Скрипт", f"Загружен скрипт: {file_path}.")
            for line_num, command_line in enumerate(commands, 1):
                command_line = command_line.strip()
                print(f"Выполняю команду (строка {line_num}): {command_line}")
                parts = command_line.split(maxsplit=1)
                command_name = parts[0]
                params_str = parts[1] if len(parts) > 1 else ""
                params = {}
                param_parts = params_str.split()
                for param_part in param_parts:
                    name, value_str = param_part.split('=', 1)
                    value = float(value_str)
                    params[name] = value

                audio_editor_method = getattr(
                    self.audio_editor, command_name, None)
                if audio_editor_method and callable(audio_editor_method):
                    if command_name == 'cut':
                        start_time = params.get('start_time')
                        end_time = params.get('end_time')
                        audio_editor_method(int(start_time), int(end_time))

                    elif command_name == 'change_speed':
                        factor = params.get('factor')
                        audio_editor_method(factor)

                    elif command_name == 'apply_reverb':
                        first_delay_seconds = params.get(
                            'first_delay_seconds')
                        first_decay_factor = params.get(
                            'first_decay_factor')
                        audio_editor_method(
                            first_delay_seconds, first_decay_factor)

                    elif command_name == 'apply_ola_pitch_shift':
                        pitch_factor = params.get('pitch_factor')
                        audio_editor_method(pitch_factor)
                    else:
                        print(f"Ошибка: Неизвестная или "
                              f"неподдерживаемая команда "
                              f"'{command_name}' в строке {line_num}.")

            messagebox.showinfo(
                "Скрипт", f"Выполнение скрипта завершено.\n")
            if self.audio_editor:
                self.time_slider.config(to=self.audio_editor.seconds)
                self.stop()

        except FileNotFoundError:
            messagebox.showerror(
                "Ошибка", f"Файл скрипта не найден: {file_path}")

    def speed(self):
        speed = float(self.speed_factor.get())
        self.audio_editor.change_speed(speed)
        self.time_slider.config(to=self.audio_editor.seconds)
        self.stop()
        self.update_last_action(f"Изменение скорости (x{speed})")

    def cut(self):
        start_time = self.start_time_entry.get()
        end_time = self.end_time_entry.get()
        if start_time == "":
            start_time = 0
        else:
            start_time = float(start_time)
        if end_time == "":
            end_time = self.audio_editor.seconds
        else:
            end_time = float(end_time)
        self.audio_editor.cut(start_time, end_time)
        self.time_slider.config(to=self.audio_editor.seconds)
        self.stop()
        self.update_last_action(f"Обрезка ({start_time}-{end_time}сек)")

    def combine_audio(self):
        file_path = tk.filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav")])
        self.audio_editor.combine(file_path)
        self.time_slider.config(to=self.audio_editor.seconds)
        self.stop()
        self.update_last_action(f"Склеено с: {file_path}")

    def apply_reverb_gui(self):
        """
        Обрабатывает нажатие кнопки "Применить реверберацию".
        """
        if not self.audio_editor:
            return
        delay = float(self.reverb_delay_entry.get())
        decay = float(self.reverb_decay_entry.get())
        self.audio_editor.apply_reverb(delay, decay)

        self.time_slider.config(to=self.audio_editor.seconds)
        self.stop()
        self.update_last_action(f"Реверберация (задержка: {delay}с)")

    def apply_pitch_shift_gui(self):
        """
        Обрабатывает нажатие кнопки "Изменить Тон".
        """
        if not self.audio_editor:
            return

        pitch_factor = float(self.pitch_factor_entry.get())
        self.audio_editor.apply_ola_pitch_shift(pitch_factor)
        self.time_slider.config(to=self.audio_editor.seconds)
        self.stop()
        self.update_last_action(f"Изменен тон на {pitch_factor}")


    def undo(self):
        self.audio_editor.undo()
        self.time_slider.config(to=self.audio_editor.seconds)
        self.stop()
        self.update_last_action(f"Последнее действие отменено")


    def redo(self):
        self.audio_editor.redo()
        self.time_slider.config(to=self.audio_editor.seconds)
        self.stop()
        self.update_last_action(f"Применили отмененное действие")


    def export(self):
        file_path = tk.filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 Files", "*.mp3"), ("WAV Files", "*.wav")])
        if file_path:
            self.audio_editor.export(file_path)

    def update_time(self, val):
        if self.audio_editor and self.is_playing:
            current_time = float(val)
            pygame.mixer.music.set_pos(current_time)

    def play(self):
        if self.audio_editor:
            pygame.mixer.music.load(self.audio_editor.file_path)
            pygame.mixer.music.play()
            self.is_playing = True
            self.update_slider_thread = threading.Thread(
                target=self.update_slider)
            self.update_slider_thread.start()
            self.play_button.config(text="⏯", command=self.pause)

    def update_slider(self):
        while self.is_playing:
            if pygame.mixer.music.get_busy():
                self.time_slider.set(pygame.mixer.music.get_pos() / 1000)
                time.sleep(1)
            else:
                self.is_playing = False
                break

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.time_slider.set(0)
        self.play_button.config(text="▶", command=self.play)

    def pause(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.is_playing = False
        else:
            pygame.mixer.music.unpause()
            self.is_playing = True
            self.update_slider_thread = threading.Thread(
                target=self.update_slider)
            self.update_slider_thread.start()

    def update_last_action(self, action):
        """Обновляет label с последним действием"""
        self.last_action_label.config(text=f"Последнее действие: {action}")
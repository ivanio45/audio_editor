from tkinter import messagebox


class HistoryManager:
    def __init__(self, initial_state):
        self.history = [initial_state]
        self.current_index = 0

    def add_state(self, state):
        self.history = self.history[:self.current_index + 1]
        self.history.append(state)
        self.current_index += 1

    def can_undo(self):
        return self.current_index > 0

    def get_previous_state(self):
        if self.can_undo():
            self.current_index -= 1
            return self.history[self.current_index]
        else:
            messagebox.showinfo("Информация", "Нет изменений для отмены.")
            return None

    def can_redo(self):
        return self.current_index < len(self.history) - 1

    def get_next_state(self):
        if self.can_redo():
            self.current_index += 1
            return self.history[self.current_index]
        else:
            messagebox.showinfo("Информация", "Нет изменений для повтора.")
            return None

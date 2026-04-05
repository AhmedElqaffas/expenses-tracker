from textual.widgets import RichLog


class MainTextArea(RichLog):
    can_focus = False
    def __init__(self, id: str):
        super().__init__(id=id, markup=True, highlight=False, wrap=True)

    def add_message(self, message: str):
        self.write(message)



class Item:

    def __init__(self, option):
        self.title = option['text']
        self.value = option['value']

    def toJSON(self):
        return {
            "title": self.title,
            "value": self.value,
        }

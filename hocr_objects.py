class Word:
    def __init__(self, text, pos0: int, pos1: int, pos2: int, pos3: int, line=None):
        self.text = text
        self.setPosition(pos0, pos1, pos2, pos3)
        self.line = line

    def __repr__(self):
        return self.text + ' [' + 'Left:' + str(self.posLeft) + ' Top:' + str(self.posTop) + ' Right:' + str(self.posRight) + ' Bottom:' + str(self.posBottom) + ']'

    def setPosition(self, pos0, pos1, pos2, pos3):
        self.posLeft = int(pos0)
        self.posTop = int(pos1)
        self.posRight = int(pos2)
        self.posBottom = int(pos3)

    def setText(self, newText):
        self.text = newText


class LineObject:
    def __init__(self, id, pos0: int, pos1: int, pos2: int, pos3: int):
        self.words = []
        self.id = id
        self.setPosition(pos0, pos1, pos2, pos3)

    def __repr__(self):
        words = ''
        for i in self.words:
            words += '\t' + str(i) + '\n'
        return 'Line -----' + self.id + '\n' + words

    def setPosition(self, pos0, pos1, pos2, pos3):
        self.posLeft = int(pos0)
        self.posTop = int(pos1)
        self.posRight = int(pos2)
        self.posBottom = int(pos3)

    def addWord(self, word):
        if(word not in self.words):
            self.words.append(word)

    def removeWord(self, word):
        if(word in self.words):
            self.words.remove(word)

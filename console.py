class ConsoleOBJ:
    buffer = []
    max_buffer_length = 100
    def out(self, string, print_too = True):
        string = str(string)
        if print_too:
            print(string)
        self.buffer.append(string)
        while len(self.buffer) > self.max_buffer_length:
            self.buffer.remove(self.buffer[0])

console = ConsoleOBJ()
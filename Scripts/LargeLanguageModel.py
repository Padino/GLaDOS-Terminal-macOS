import re, ollama, os, threading, queue

class LargeLanguageModel:
    def __init__(self, ModelName, SystemPrompt):
        self.Model = ModelName
        self.History = [{"role":"system", "content":SystemPrompt}]

        self.ResponseQueue = queue.Queue()
        self.InferenceThread = None
        self.IsProcessing = False
        
        # Warm start the model
        ollama.chat(model=self.Model, messages=[{"role":"user", "content":"Say one word."}])

    def ClearHistory(self, SystemPrompt):
        self.History = [{"role":"system", "content":SystemPrompt}]

    def StartInference(self, Text):
        if not self.IsProcessing:
            self.IsProcessing = True
            self.InferenceThread = threading.Thread(target=self.InferenceTask, args=(Text,))
            self.InferenceThread.daemon = True
            self.InferenceThread.start()

    def InferenceTask(self, Text):
        try:
            # Get response and appendend all to history
            self.History.append({"role":"user", "content":Text})
            Response = ollama.chat(model=self.Model, messages=self.History)
            self.History.append(Response["message"])

            # Remove new lines
            CleanedText = Response["message"]["content"].replace("\n", " ")
            # Remove excessive white space
            CleanedSentence = re.sub(r'\s+', ' ', CleanedText)
            # Remove white space from start and end of it plus lower case
            CleanedSentence = CleanedText.lower().strip()
            # Add a full stop
            if CleanedText[-1] != ".": CleanedText += "."

            self.ResponseQueue.put(CleanedText)

        finally:
            self.IsProcessing = False

    def CheckResponse(self):
        try:
            Response = self.ResponseQueue.get_nowait()
            return True, Response
        except queue.Empty:
            return False, None

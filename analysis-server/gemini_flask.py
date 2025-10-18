# Library can be installed with "pip install -q -U google-genai"
from google import genai

# GeminiResponse
class GeminiResponse:
    def __init__(self):
        self.KEY = "AIzaSyC10UAVHV3Ff4SYuTdkXk_BI47Op_UodjM"
        self.client = genai.Client(api_key=self.KEY)

    def generateResponse(self, prompt):
        return self.client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt,
        )

    def setNewKey(self, new_key):
        self.KEY = new_key
        self.client = genai.Client(api_key=self.KEY)

# gen = GeminiResponse()
# print(gen.generateResponse("Generate a poem about apples"))


# Function to extract questions after think tag
def extract_questions_after_think(text):
        if "</think>" in text:
            return text.split("</think>", 1)[1].strip()
        return text.strip()
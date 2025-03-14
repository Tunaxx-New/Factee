import base64
from PIL import Image
import io
import openai
from app import create_app

app = create_app()


class GptService:
    def __init__(self):
        openai.api_key = app.config["OPENAI_API_KEY"]

    # Function to get AI feedback on the differences
    def get_ai_feedback(self, image_path1, image_path2, task, enviroment):
        prompt = f"""
                Image that your worker process educational task. Please check their result based on task description and 2 images comparing.
                
                Enviroment, where worker works:
                {enviroment}
                
                Task description:
                {task}
                
                Provide a similarity score from 0 to 1 with 2 digits after dot, where 0 means completely different and wrong and 1 means ideal.
    
                Please return the response in the following format:
                {{
                    "similarity_score": <score>,
                    "feedback": "<explanation of the similarities and differences>",
                    "suggestions": "<possible solutions or advices to solve problem>",
                    "code": "<some code in {enviroment} to complete {task}>"
                }}
    
                Make sure to include both the score and feedback in the response.
                """

        # Call the OpenAI API (replace YOUR_API_KEY with your actual OpenAI API key)
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # or "gpt-4"
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "text", "text": "First screenshot with right solution of task"},
                {"type": "image_url", "image_url": {"url": image_path1}},
                {"type": "text", "text": "Second screenshot. The worker solution"},
                {"type": "image_url", "image_url": {"url": image_path2}},
            ]}, {
                          "role": "system",
                          "content": [
                              {"type": "text", "text": "You are a helpful assistant that responds in Russian."},
                              {"type": "text", "text": "Do not mention first image in feedback"},
                              {"type": "text", "text": "Address the employee as \"you\". Respectfully."},
                          ]
                      }]
        )

        return response['choices'][0]['message']['content']

    def g(self):
        # Sample texts for comparison
        text1 = "The following function adds two numbers: def add(a, b): return a + b. This function returns the sum of a and b."
        text2 = "This function calculates the total of two inputs: def sum(x, y): return x + y + 1. It returns the sum but with an error."

        feedback = self.get_ai_feedback("https://static.1c.ru/news/images/img28446-2.png",
                                        "https://static.1c.ru/news/images/img28446-11.png",
                                        "Создать конфигурацию для отображения студентов с фильтром по организациям.",
                                        "1с конфигуратор")
        print(feedback)

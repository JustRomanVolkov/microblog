import os
import requests
import json
import time


# Импортируем необходимые библиотеки: os для доступа к переменным окружения, requests для выполнения HTTP-запросов, json для работы с данными в формате JSON.

def send_request_to_openai(prompt):
    # Определяем функцию для отправки запросов к OpenAI API.
    headers = {
        'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}',
        'Content-Type': 'application/json',
    }
    # Устанавливаем заголовки запроса, включая токен авторизации.

    data = {
        'model': os.getenv('MODEL', 'text-davinci-003'),
        'prompt': prompt,
        'temperature': float(os.getenv('TEMPERATURE', 0)),
        'max_tokens': int(os.getenv('MAX_TOKENS', 50)),
        'top_p': float(os.getenv('TOP_P', 0.7)),
        'frequency_penalty': float(os.getenv('FREQUENCY_PENALTY', 0)),
        'presence_penalty': float(os.getenv('PRESENCE_PENALTY', 0)),
    }
    
    max_retries = 5
    retry_delay = 30  # Время задержки в секундах
    
    
    # Формируем тело запроса с параметрами для модели OpenAI.

    for i in range(max_retries):
        # Выполняем POST-запрос к API.
        response = requests.post('https://api.openai.com/v1/completions', headers=headers, json=data)

        if response.status_code == 429:
            if i < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                raise Exception("API rate limit exceeded and max retries reached.")
        response.raise_for_status() # Проверяем ответ на наличие ошибок.
        return response.json()['choices'][0]['text'].strip()    
        # Возвращаем текстовый ответ от OpenAI, очищенный от пробелов.


def post_comment_to_pr(comment_body, pull_request_number):
    # Определяем функцию для создания комментария в пулл-реквесте на GitHub.
    github_token = os.getenv('GITHUB_TOKEN')
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    # Устанавливаем заголовки запроса, включая токен авторизации GitHub.
    print(f"GITHUB_REPOSITORY: {os.getenv('GITHUB_REPOSITORY')}")


    pr_comment_url = f'https://api.github.com/repos/{os.getenv("GITHUB_REPOSITORY")}/issues/{pull_request_number}/comments'
    # Формируем URL для создания комментария на GitHub.

    response = requests.post(pr_comment_url, headers=headers, json={'body': comment_body})
    # Выполняем POST-запрос к GitHub API для создания комментария.

    response.raise_for_status()  # Проверяем ответ на наличие ошибок.


if __name__ == "__main__":
    # Получаем данные события из файла события, который предоставляет GitHub
    with open(os.getenv('GITHUB_EVENT_PATH')) as event_file:
        event_data = json.load(event_file)
        print(json.dumps(event_data, indent=4))  # Для наглядности структуры JSON

    pull_request_number = event_data['pull_request']['number'] # Получаем номер пулл-реквеста из данных события

    # Проверяем, является ли файл исполняемым, и запускаем основную логику скрипта.
    prompt = os.getenv('PROMPT', 'Please review the following code for any issues or suggestions for improvements:')
    # Получаем подсказку из переменной окружения или используем значение по умолчанию.

    try:
        review_comment = send_request_to_openai(prompt)
        # Отправляем запрос к OpenAI и получаем ревью кода.
        post_comment_to_pr(review_comment, pull_request_number)
        # Создаём комментарий к пулл-реквесту с полученным ревью.
        print("Review comment posted successfully.")
        # Выводим сообщение об успешной отправке комментария.
    except Exception as e:
        print(f"Failed to post review comment: {e}")
        # В случае возникновения ошибки выводим сообщение.
        

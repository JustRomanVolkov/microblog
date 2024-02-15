import os
import requests
import json
import time


# Функция для извлечения текста из PR
def extract_gpt_prompts_as_single_text(owner, repo, pull_number, session=None):
    if session is None:
        session = requests.Session()
    prompts = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files?page={page}"
        response = session.get(url)
        response.raise_for_status()
        files_data = response.json()
        if not files_data:
            break
        for file in files_data:
            filename = file['filename']
            if 'patch' in file:
                patch_text = file['patch']
                prompts.append(f"File: {filename}\n{patch_text}")
        page += 1
    combined_text = "\n\n".join(prompts)
    return combined_text


# Формирование запроса к ChatGPT
def send_prompt_to_chatgpt(api_key, model, system_prompt, user_prompt, pull_reqeust, url):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": f"{system_prompt}"},
            {"role": "user", "content": f"{user_prompt}:\n{pull_reqeust}"},
        ],
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        response_data = response.json()
        return response_data['choices'][0]['message']['content']
    else:
        return f"Ошибка: {response.status_code}"


# Функция для добавления комментария к PR
def add_comment_to_pr(owner, repo, pull_number, body, token):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pull_number}/comments"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}"
    }
    response = requests.post(url, headers=headers, json={"body": body})
    response.raise_for_status()


if __name__ == "__main__":
    try:
        # Загрузка переменных среды из GitHub Secrets
        OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
        OPENAI_API_ENDPOINT = os.environ.get('OPENAI_API_ENDPOINT')
        GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
        GITHUB_EVENT_PATH = os.getenv('GITHUB_EVENT_PATH')
        MODEL = os.getenv('MODEL')
        SYSTEM_PROMPT = os.getenv('SYSTEM_PROMPT')
        USER_PROMPT = os.getenv('USER_PROMPT')
        
        with open(GITHUB_EVENT_PATH, 'r') as file:
            event_data = json.load(file)
        owner = event_data['repository']['owner']['login']
        repo = event_data['repository']['name']
        pull_number = event_data['pull_request']['number']

        # Получение данных для отправки в ChatGPT
        pull_reqeust = extract_gpt_prompts_as_single_text(owner, repo, pull_number)

        # Отправка запроса и получение ответа
        response_text = send_prompt_to_chatgpt(OPENAI_API_KEY, MODEL, SYSTEM_PROMPT, USER_PROMPT, pull_reqeust, OPENAI_API_ENDPOINT)

        # Добавление комментария к PR
        add_comment_to_pr(owner, repo, pull_number, response_text, GITHUB_TOKEN)
        
    except Exception as e:
        print(f"Failed to post review comment: {e}")

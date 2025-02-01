import gradio as gr
import subprocess
import requests


DEEPL_API_KEY = "DEEPL_API_KEY"  # 여기에 DeepL API 키를 입력하세요.


# DeepL API를 사용해 텍스트를 번역하는 함수
def translate_text(text, source_lang, target_lang):
    """
    텍스트를 source_lang에서 target_lang으로 번역합니다.
    Args:
        text (str): 번역할 텍스트
        source_lang (str): 원본 언어 코드 (예: "KO", "EN")
        target_lang (str): 대상 언어 코드 (예: "EN", "KO")
    Returns:
        str: 번역된 텍스트 또는 에러 메시지
    """
    if not DEEPL_API_KEY:
        return "Translation Error: API Key is missing"  # API 키가 없을 때 에러 처리
    url = "https://api-free.deepl.com/v2/translate"
    headers = {"Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"}
    data = {
        "text": text,
        "source_lang": source_lang,
        "target_lang": target_lang,
    }
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
        return response.json()["translations"][0]["text"]  # 번역된 텍스트 반환
    except requests.exceptions.RequestException as e:
        return f"Translation Error: {str(e)}"  # 요청 실패 시 에러 메시지 반환


# 입력 텍스트를 언어 설정에 따라 처리
def process_prompt(prompt, language, translate_to_english=True):
    """
    입력 텍스트를 번역하거나 그대로 반환합니다.
    Args:
        prompt (str): 사용자 입력 텍스트
        language (str): 선택된 언어 ("English" 또는 "Korean")
        translate_to_english (bool): True면 영어로 번역, False면 그대로 반환
    Returns:
        str: 번역된 또는 원본 텍스트
    """
    if language == "Korean" and translate_to_english:
        return translate_text(prompt, "KO", "EN")  # 한글을 영어로 번역
    return prompt  # 번역 필요 없으면 원본 반환


# Deepseek의 응답을 언어 설정에 따라 처리
def process_response(response, language, translate_to_korean=True):
    """
    모델 응답 텍스트를 번역하거나 그대로 반환합니다.
    Args:
        response (str): 모델의 응답 텍스트
        language (str): 선택된 언어 ("English" 또는 "Korean")
        translate_to_korean (bool): True면 한글로 번역, False면 그대로 반환
    Returns:
        str: 번역된 또는 원본 텍스트
    """
    if language == "Korean" and translate_to_korean:
        return translate_text(response, "EN", "KO")  # 영어를 한글로 번역
    return response  # 번역 필요 없으면 원본 반환


# Deepseek 모델 실행 및 결과 반환
def ask_deepseek(prompt, language):
    """
    사용자 입력을 Deepseek에 전달하고 결과를 반환합니다.
    Args:
        prompt (str): 사용자 입력 텍스트
        language (str): 선택된 언어 ("English" 또는 "Korean")
    Returns:
        str: Deepseek의 응답 텍스트
    """
    # 입력 텍스트를 필요에 따라 영어로 번역
    prompt = process_prompt(prompt, language, translate_to_english=True)
    try:
        # Deepseek 실행 "deepseek-ai/deepseek-llm" 해당 부분을 수정하여 원하는 모델을 입력하세요.
        result = subprocess.run(
            ["ollama", "run", "deepseek-ai/deepseek-llm", prompt],
            capture_output=True, text=True, check=True
        )
        response = result.stdout.strip()  # 모델의 출력 결과 가져오기
    except subprocess.CalledProcessError as e:
        response = f"Deepseek Error: {e.stderr.strip()}"  # 실행 오류 시 처리
    # 결과를 필요에 따라 한글로 번역
    return process_response(response, language, translate_to_korean=True)


# Gradio를 통해 사용자 입력을 처리하고 대화 기록 업데이트
def interact(prompt, history, language):
    """
    사용자 입력에 대한 Deepseek 응답을 처리하고 대화 기록을 업데이트합니다.
    Args:
        prompt (str): 사용자 입력 텍스트
        history (list): 대화 기록
        language (str): 선택된 언어 ("English" 또는 "Korean")
    Returns:
        tuple: 업데이트된 대화 기록과 빈 입력 텍스트
    """
    response = ask_deepseek(prompt, language)  # Deepseek에 입력 전달
    history.append((f"User: {prompt}", f"Deepseek: {response}"))  # 대화 기록 업데이트
    return history, ""  # 대화 기록과 빈 입력창 반환


# 대화 기록 초기화
def clear_chat():
    """
    대화 기록을 초기화합니다.
    Returns:
        tuple: 빈 대화 기록과 빈 입력 텍스트
    """
    return [], ""


# Gradio UI 구성
with gr.Blocks() as demo:
    history = gr.State([])  # 대화 기록 상태 저장

    # 언어 선택 버튼
    with gr.Row():
        language = gr.Radio(["English", "Korean"], value="English", label="Language")

    # 채팅 히스토리 창
    with gr.Row():
        chatbox = gr.Chatbot(label="Chat History")

    # 사용자 입력 창과 버튼
    with gr.Row():
        user_input = gr.Textbox(
            label="User Input",
            placeholder="Type your question here and press Enter...",
            lines=3,  # 기본 입력창 높이
            max_lines=5  # 최대 입력창 높이
        )
        clear_btn = gr.Button("Clear")  # Clear 버튼

    # 이벤트 연결
    user_input.submit(interact, [user_input, history, language], [chatbox, user_input])
    clear_btn.click(clear_chat, [], [chatbox, user_input])

# Gradio 앱 실행
demo.launch()

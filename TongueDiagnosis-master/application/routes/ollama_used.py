import requests
import json
from starlette.responses import JSONResponse, StreamingResponse
from ..orm import create_new_chat_records, get_chat_record
from ..config import settings


class OllamaStreamChatter:
    def __init__(self, model=settings.LLM_NAME,
                 system_prompt=None,
                 language='en'
                 ):
        self.url = settings.OLLAMA_PATH
        self.headers = {"Content-Type": "application/json"}
        self.messages = []
        self.model = model
        self.language = language

    def chat_stream_first(self, user_input, feature, id, db, session_new_id):
        self.messages = []
        language_prompts = {
            'en': 'You are an AI traditional Chinese medicine doctor specializing in tongue diagnosis. Based on the tongue features provided, give health advice directly. Answer in English only. Be concise and practical.',
            'zh': '你是一位中医舌诊专家。根据提供的舌头特征，直接给出健康建议。用中文回答。简洁实用，不要输出思考过程。',
            'es': 'Eres un médico de medicina tradicional china especializado en diagnóstico de la lengua. Da consejos de salud directamente basándote en las características de la lengua. Responde solo en español. Sé conciso y práctico.',
            'fr': 'Vous êtes un médecin de médecine traditionnelle chinoise spécialisé dans le diagnostic de la langue. Donnez des conseils de santé directement. Répondez uniquement en français. Soyez concis et pratique.',
            'de': 'Sie sind ein Experte für traditionelle chinesische Medizin, spezialisiert auf Zungendiagnose. Geben Sie Gesundheitsberatung direkt. Antworten Sie nur auf Deutsch. Seien Sie prägnant und praktisch.',
            'ja': 'あなたは中医舌診の専門家です。舌の特徴に基づいて、直接健康アドバイスを与えてください。日本語のみで回答してください。簡潔で実用的に。',
            'ko': '당신은 한의학 혀진단 전문가입니다. 혀 특징에 따라 직접 건강 조언을 제공하세요. 한국어로만 답변하세요. 간결하고 실용적으로.'
        }
        system_prompt = language_prompts.get(self.language, language_prompts['en'])
        self.messages.append({
            "role": "system",
            "content": system_prompt
        })
        if self.language == 'en':
            self.messages.append({"role": "user", "content": f"Tongue features: {feature}. {user_input}. Give health advice in English."})
        elif self.language == 'zh':
            self.messages.append({"role": "user", "content": f"舌头特征：{feature}。{user_input}。请给出健康建议。"})
        elif self.language == 'es':
            self.messages.append({"role": "user", "content": f"Características de la lengua: {feature}. {user_input}. Da consejos de salud en español."})
        elif self.language == 'fr':
            self.messages.append({"role": "user", "content": f"Caractéristiques de la langue: {feature}. {user_input}. Donnez des conseils de santé en français."})
        elif self.language == 'de':
            self.messages.append({"role": "user", "content": f"Zungenmerkmale: {feature}. {user_input}. Geben Sie Gesundheitsberatung auf Deutsch."})
        elif self.language == 'ja':
            self.messages.append({"role": "user", "content": f"舌の特徴：{feature}。{user_input}。健康アドバイスを日本語でください。"})
        elif self.language == 'ko':
            self.messages.append({"role": "user", "content": f"혀 특징: {feature}. {user_input}. 한국어로 건강 조언을 주세요."})
        else:
            self.messages.append({"role": "user", "content": f"Tongue features: {feature}. {user_input}. Give health advice in {self.language}."})
        data = {
            "model": self.model,
            "messages": self.messages,
            "stream": True,
            "options": {
                "num_predict": 600,
                "temperature": 0.7,
                "top_p": 0.9,
                "num_ctx": 2048
            },
            "think": False
        }
        print(f"[DEBUG] 发送到 Ollama 的请求: model={self.model}")
        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                json=data,
                stream=True
            )
            response.raise_for_status()
            print(f"[DEBUG] Ollama 响应状态: {response.status_code}")

            def generate():
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            if 'message' in chunk:
                                msg = chunk['message']
                                content = msg.get('content', '')
                                if content:
                                    full_response += content
                                    yield json.dumps({
                                        "token": content,
                                        "session_id": session_new_id,
                                        "is_complete": False
                                    }) + "\n"
                        except json.JSONDecodeError as e:
                            print(f"[DEBUG] JSON 解析错误: {e}")
                print(f"[DEBUG] 流结束，完整响应长度: {len(full_response)}")
                yield json.dumps({
                    "token": full_response,
                    "session_id": session_new_id,
                    "is_complete": True
                }) + "\n"
                self._save_to_db_async(db, full_response, session_new_id)
            return StreamingResponse(
                generate(),
                media_type='application/x-ndjson'
            )
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] Ollama 请求失败: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": f"请求失败: {str(e)}"}
            )

    def chat_stream_add(self, id, db, session_id):
        chat_record = get_chat_record(ID=id, sessionid=session_id, db=db)
        
        if isinstance(chat_record, int) and chat_record in [102, 103]:
            error_messages = {
                102: "会话不存在或不属于该用户",
                103: "会话中没有聊天记录"
            }
            return JSONResponse(
                status_code=500,
                content={"error": error_messages.get(chat_record, "未知错误")}
            )
        
        records = []
        for record in chat_record:
            role = "user" if record.role == 1 else "assistant"
            records.append({"role": role, "content": record.content})
        
        language_prompts = {
            'en': 'You are an AI traditional Chinese medicine doctor. Continue the conversation and give health advice directly. Answer in English only. Be concise.',
            'zh': '你是一位中医舌诊专家。继续对话，直接给出健康建议。用中文回答。简洁实用，不要输出思考过程。',
            'es': 'Eres un médico de medicina tradicional china. Continúa la conversación y da consejos directamente. Responde solo en español.',
            'fr': 'Vous êtes un médecin de médecine traditionnelle chinoise. Continuez la conversation et donnez des conseils directement. Répondez uniquement en français.',
            'de': 'Sie sind ein Experte für traditionelle chinesische Medizin. Setzen Sie das Gespräch fort und geben Sie Beratung direkt. Antworten Sie nur auf Deutsch.',
            'ja': 'あなたは中医舌診の専門家です。会話を続け、直接アドバイスを与えてください。日本語のみで回答してください。',
            'ko': '당신은 한의학 전문가입니다. 대화를 계속하고 직접 조언을 제공하세요. 한국어로만 답변하세요.'
        }
        system_prompt = language_prompts.get(self.language, language_prompts['en'])
        
        self.messages = []
        self.messages.append({"role": "system", "content": system_prompt})
        
        for record in records:
            self.messages.append(record)
        
        data = {
            "model": self.model,
            "messages": self.messages,
            "stream": True,
            "options": {
                "num_predict": 600,
                "temperature": 0.7,
                "top_p": 0.9,
                "num_ctx": 2048
            },
            "think": False
        }
        print(f"[DEBUG] chat_stream_add 发送到 Ollama 的请求: model={self.model}")
        try:
            response = requests.post(self.url, headers=self.headers, json=data, stream=True)
            response.raise_for_status()
            print(f"[DEBUG] chat_stream_add Ollama 响应状态: {response.status_code}")

            def generate():
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            if 'message' in chunk:
                                msg = chunk['message']
                                content = msg.get('content', '')
                                if content:
                                    full_response += content
                                    yield json.dumps({
                                        "token": content,
                                        "session_id": session_id,
                                        "is_complete": False
                                    }) + "\n"
                        except json.JSONDecodeError as e:
                            print(f"[DEBUG] JSON 解析错误: {e}")
                print(f"[DEBUG] chat_stream_add 流结束，完整响应长度: {len(full_response)}")
                yield json.dumps({
                    "token": full_response,
                    "session_id": session_id,
                    "is_complete": True
                }) + "\n"
                self._save_to_db_async(db, full_response, session_id)
            return StreamingResponse(
                generate(),
                media_type='application/x-ndjson'
            )
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] chat_stream_add Ollama 请求失败: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": f"请求失败: {str(e)}"}
            )

    def _save_to_db_async(self, db, content, session_id):
        import threading
        from ..models.database import SessionLocal
        
        def save_task():
            new_db = SessionLocal()
            try:
                create_new_chat_records(
                    db=new_db,
                    content=content,
                    session_id=session_id,
                    role=2
                )
                new_db.commit()
                print(f"[DEBUG] 数据库保存成功: session_id={session_id}, content_length={len(content)}")
            except Exception as e:
                new_db.rollback()
                print(f"数据库保存失败: {e}")
            finally:
                new_db.close()

        threading.Thread(target=save_task).start()

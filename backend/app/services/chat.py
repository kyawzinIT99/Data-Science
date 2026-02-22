import uuid
import json
import os
from datetime import datetime, timezone
from openai import OpenAI
from fastapi import HTTPException

from app.core.config import settings
from app.core.database import chats_table, Chat
from app.services.chunker import load_vectorstore
from app.services.language import detect_language, get_chat_system_prompt
from app.models.schemas import ChatResponse, ChatSession
from app.services.forecast import PriceForecaster
from app.services.file_parser import SUPPORTED_EXTENSIONS
import logging
logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def _find_file_path(file_id: str) -> str:
    for ext in SUPPORTED_EXTENSIONS:
        path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")
        if os.path.exists(path):
            return path
        legacy_path = os.path.join("./uploads", f"{file_id}{ext}")
        if os.path.exists(legacy_path):
            return legacy_path
    return None

def generate_forecast(file_id: str, date_column: str = "Date", price_column: str = "Price", months: int = 3):
    """
    Generate a price forecast for a given file.
    """
    file_path = _find_file_path(file_id)
    if not file_path:
        return {"error": "File not found"}

    try:
        ext = os.path.splitext(file_path)[1].lower()
        
        # --- Modal Remote Execution Hook ---
        from app.utils.modal import get_modal_func
        modal_forecast_run = get_modal_func("run_forecast")
        
        if modal_forecast_run:
            try:
                from app.utils.modal import sync_file_to_modal
                if sync_file_to_modal(file_id, file_path):
                    logger.info(f"Offloading chat forecast to Modal (via Volume: {file_id})...")
                    remote_result = modal_forecast_run.remote(
                        file_id=file_id,
                        file_ext=ext,
                        date_col=date_column,
                        value_col=price_column
                    )
                else:
                    logger.info("Offloading chat forecast to Modal (via direct content)...")
                    with open(file_path, "rb") as f:
                        file_content = f.read()
                    remote_result = modal_forecast_run.remote(
                        file_id=file_id,
                        file_ext=ext,
                        date_col=date_column,
                        value_col=price_column,
                        file_content=file_content
                    )
                return {
                    "forecast": remote_result["forecast"],
                    "metrics": remote_result["metrics"]
                }
            except Exception as e:
                logger.warning(f"Modal chat forecast failed, falling back to local: {e}")

        # Local Fallback
        forecaster = PriceForecaster(
            file_path=file_path,
            date_column=date_column,
            price_column=price_column
        )
        forecaster.load_data()
        metrics = forecaster.train_model()
        forecast_df = forecaster.predict_next_months(months)
        
        forecast_data = []
        for _, row in forecast_df.iterrows():
            f_date = row["Forecast_Date"]
            if hasattr(f_date, "strftime"):
                f_date = f_date.strftime("%Y-%m-%d")
                
            forecast_data.append({
                "date": str(f_date),
                "price": round(float(row["Predicted_Price"]), 2)
            })
            
        return {
            "forecast": forecast_data,
            "metrics": metrics
        }
    except Exception as e:
        return {"error": str(e)}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_forecast",
            "description": "Generate a future price forecast based on a date and price column in a data file (CSV or Excel).",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_column": {
                        "type": "string",
                        "description": "Name of the date column (default: Date)"
                    },
                    "price_column": {
                        "type": "string",
                        "description": "Name of the price column (default: Price)"
                    },
                    "months": {
                        "type": "integer",
                        "description": "Number of months to forecast (default: 3)"
                    }
                }
            }
        }
    }
]

def chat_with_document(
    file_id: str, question: str, chat_history: list[dict], session_id: str | None = None, language: str | None = None
) -> ChatResponse:
    if session_id:
        session_doc = chats_table.get(Chat.session_id == session_id)
        if session_doc:
            chat_history = session_doc.get("messages", [])
    else:
        session_id = str(uuid.uuid4())

    vectorstore = load_vectorstore(file_id)
    results = vectorstore.similarity_search(question, k=4)
    context_chunks = [doc.page_content for doc in results]
    context = "\n\n---\n\n".join(context_chunks)

    lang_code = language
    if not lang_code:
        lang_code, _ = detect_language(context)
        
    system_content = get_chat_system_prompt(lang_code, context)
    # Add explicit tool instruction to system prompt
    system_content += "\n\nYou have access to tools. If the user asks for a forecast or prediction, use the 'generate_forecast' tool. Always mention you are using the forecasting model."

    messages = [{"role": "system", "content": system_content}]
    for entry in chat_history[-10:]:
        messages.append({"role": entry["role"], "content": entry["content"]})
    messages.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model=settings.CHAT_MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.2,
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        messages.append({
            "role": response_message.role,
            "content": response_message.content,
            "tool_calls": [
                {
                    "id": t.id,
                    "type": t.type,
                    "function": {
                        "name": t.function.name,
                        "arguments": t.function.arguments,
                    }
                } for t in tool_calls
            ]
        })
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            if function_name == "generate_forecast":
                tool_result = generate_forecast(
                    file_id=file_id,
                    date_column=function_args.get("date_column", "Date"),
                    price_column=function_args.get("price_column", "Price"),
                    months=function_args.get("months", 3)
                )
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(tool_result),
                })
        
        # Second call to LLM with tool results
        second_response = client.chat.completions.create(
            model=settings.CHAT_MODEL,
            messages=messages,
        )
        answer = second_response.choices[0].message.content
    else:
        answer = response_message.content

    now = datetime.now(timezone.utc).isoformat()
    new_messages = chat_history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ]

    existing = chats_table.get(Chat.session_id == session_id)
    if existing:
        chats_table.update({"messages": new_messages, "updated_at": now}, Chat.session_id == session_id)
    else:
        title = question[:60] + ("..." if len(question) > 60 else "")
        chats_table.insert({
            "session_id": session_id,
            "file_id": file_id,
            "title": title,
            "messages": new_messages,
            "created_at": now,
            "updated_at": now,
        })

    return ChatResponse(
        answer=answer,
        sources=[chunk[:200] + "..." for chunk in context_chunks],
        session_id=session_id,
    )

def get_chat_sessions(file_id: str) -> list[ChatSession]:
    docs = chats_table.search(Chat.file_id == file_id)
    sessions = []
    for d in sorted(docs, key=lambda x: x.get("updated_at", ""), reverse=True):
        sessions.append(ChatSession(
            session_id=d["session_id"],
            file_id=d["file_id"],
            title=d["title"],
            messages=d["messages"],
            created_at=d["created_at"],
            updated_at=d["updated_at"],
        ))
    return sessions

def get_chat_session(session_id: str) -> ChatSession | None:
    d = chats_table.get(Chat.session_id == session_id)
    if not d:
        return None
    return ChatSession(
        session_id=d["session_id"],
        file_id=d["file_id"],
        title=d["title"],
        messages=d["messages"],
        created_at=d["created_at"],
        updated_at=d["updated_at"],
    )

def delete_chat_session(session_id: str) -> bool:
    removed = chats_table.remove(Chat.session_id == session_id)
    return len(removed) > 0

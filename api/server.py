"""
server.py — Main FastAPI server for Orrbit.

Handles:
- Authentication (register, login via auth_routes)
- Chat with full memory and personalization
- Each user gets isolated memory and profile
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
import json

from dotenv import load_dotenv
load_dotenv()

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph.builder import agent
from tools.input_guard import validate_input
from auth.auth_handler import get_current_user_id, get_current_user_optional
from auth.auth_routes import router as auth_router
from auth.models import init_db, get_user_by_id
from memory.conversation_memory import get_session
from memory.long_term_memory import get_user_memory
from memory.user_profile import get_user_profile

# ── App setup ──────────────────────────────────────────────────────────────────

app = FastAPI(title="Orrbit AI Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register auth routes (/auth/register, /auth/login, /auth/me, /auth/logout)
app.include_router(auth_router)

# Initialize MongoDB on startup
@app.on_event("startup")
def startup():
    init_db()
    print("[Orrbit] Server started successfully ✓")


# ── Request / Response schemas ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message:    str
    session_id: str = "default"


class ChatResponse(BaseModel):
    answer:          str
    domain:          str
    warning:         str = ""
    used_web_search: bool = False
    username:        str = ""


# ── Chat endpoint ──────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    user_id: str = Depends(get_current_user_optional),
):
    """
    Main chat endpoint.
    - Validates input
    - Loads conversation history, long-term memory, and user profile
    - Runs the LangGraph agent
    - Updates memory and profile after response
    """

    # ── Step 1: Input validation ───────────────────────────────────────────────
    validation = validate_input(request.message)
    if not validation.valid:
        return ChatResponse(
            answer=validation.error,
            domain="system",
        )

    # ── Step 2: Load memory and profile (if user is logged in) ────────────────
    conversation = get_session(request.session_id)
    long_term    = get_user_memory(user_id)    if user_id else None
    profile      = get_user_profile(user_id)   if user_id else None
    username     = ""

    if user_id:
        user = get_user_by_id(user_id)
        username = user.get("username", "") if user else ""

    # ── Step 3: Build context from memory ─────────────────────────────────────
    memory_context = ""

    # Add long-term memory context
    if long_term:
        lt_summary = long_term.get_context_summary()
        if lt_summary:
            memory_context += lt_summary + "\n\n"

    # Add conversation history
    history_text = conversation.get_history_as_text()
    if history_text:
        memory_context += history_text

    # Add profile personalization
    profile_addon = profile.get_system_prompt_addon() if profile else ""

    # ── Step 4: Build enriched query ──────────────────────────────────────────
    # If it's a follow-up question, prepend history so agent understands context
    enriched_query = validation.cleaned
    if conversation.is_followup(validation.cleaned) and history_text:
        enriched_query = (
            f"{history_text}\n\n"
            f"Current question: {validation.cleaned}"
        )

    # ── Step 5: Run the agent ──────────────────────────────────────────────────
    try:
        initial_state = {
            "messages":          [HumanMessage(content=enriched_query)],
            "domain":            "",
            "user_query":        validation.cleaned,
            "retrieved_context": memory_context,
            "final_answer":      "",
            "used_web_search":   False,
            "metadata": {
                "user_id":       user_id or "anonymous",
                "username":      username,
                "profile_addon": profile_addon,
            },
        }

        output = agent.invoke(initial_state)
        answer = output["final_answer"]
        domain = output.get("domain", "general")
        used_web = output.get("used_web_search", False)

    except Exception as e:
        print(f"[Error] Agent failed: {e}")
        return ChatResponse(
            answer="Something went wrong. Please try again.",
            domain="system",
        )

    # ── Step 6: Update memory ──────────────────────────────────────────────────
    # Save to conversation history (all users)
    conversation.add_user_message(validation.cleaned)
    conversation.add_assistant_message(answer, domain=domain)

    # Save to long-term memory and update profile (logged-in users only)
    if user_id and long_term and profile:
        long_term.extract_and_remember(validation.cleaned, answer)
        profile.update_from_message(validation.cleaned, domain)

    # ── Step 7: Return response ────────────────────────────────────────────────
    return ChatResponse(
        answer=answer,
        domain=domain,
        warning=validation.warning,
        used_web_search=used_web,
        username=username,
    )


# ── Streaming chat endpoint ──────────────────────────────────────────────────────

def _prepare_chat_state(request: "ChatRequest", user_id: str | None):
    """
    Shared setup logic used by both /chat and /chat/stream.
    Validates input, loads memory/profile, builds the initial graph state.
    Returns (validation, conversation, long_term, profile, username, initial_state)
    or (validation, None, None, None, None, None) if validation failed.
    """
    validation = validate_input(request.message)
    if not validation.valid:
        return validation, None, None, None, None, None

    conversation = get_session(request.session_id)
    long_term    = get_user_memory(user_id)  if user_id else None
    profile      = get_user_profile(user_id) if user_id else None
    username     = ""

    if user_id:
        user = get_user_by_id(user_id)
        username = user.get("username", "") if user else ""

    memory_context = ""
    if long_term:
        lt_summary = long_term.get_context_summary()
        if lt_summary:
            memory_context += lt_summary + "\n\n"

    history_text = conversation.get_history_as_text()
    if history_text:
        memory_context += history_text

    profile_addon = profile.get_system_prompt_addon() if profile else ""

    enriched_query = validation.cleaned
    if conversation.is_followup(validation.cleaned) and history_text:
        enriched_query = f"{history_text}\n\nCurrent question: {validation.cleaned}"

    initial_state = {
        "messages":          [HumanMessage(content=enriched_query)],
        "domain":            "",
        "user_query":        validation.cleaned,
        "retrieved_context": memory_context,
        "final_answer":      "",
        "used_web_search":   False,
        "metadata": {
            "user_id":       user_id or "anonymous",
            "username":      username,
            "profile_addon": profile_addon,
        },
    }

    return validation, conversation, long_term, profile, username, initial_state


@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    user_id: str = Depends(get_current_user_optional),
):
    """
    Streaming version of /chat. Sends tokens as they're generated by the
    domain node's LLM, using Server-Sent Events (SSE).

    Event format sent to the client:
        data: {"type": "token", "content": "..."}
        data: {"type": "domain", "domain": "computing"}
        data: {"type": "done"}
        data: {"type": "error", "message": "..."}
    """
    validation, conversation, long_term, profile, username, initial_state = (
        _prepare_chat_state(request, user_id)
    )

    if not validation.valid:
        async def error_stream():
            yield f"data: {json.dumps({'type': 'token', 'content': validation.error})}\n\n"
            yield f"data: {json.dumps({'type': 'domain', 'domain': 'system'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

    async def event_stream():
        full_answer = ""
        domain_sent = False
        final_domain = "general"

        try:
            # stream_mode="messages" yields (message_chunk, metadata) tuples
            # for every LLM token generated by any node in the graph.
            async for chunk, metadata in agent.astream(
                initial_state, stream_mode="messages"
            ):
                # Only forward actual content tokens (skip empty/control chunks)
                token = getattr(chunk, "content", "") or ""
                if token:
                    full_answer += token
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

                # Domain becomes available once the router node has run —
                # surface it to the frontend as soon as we know it.
                node_name = metadata.get("langgraph_node", "")
                if not domain_sent and node_name and node_name not in ("router", "rag", "web_search"):
                    final_domain = node_name
                    domain_sent = True
                    yield f"data: {json.dumps({'type': 'domain', 'domain': final_domain})}\n\n"

            # ── Persist memory after the full answer has streamed ──────────────
            conversation.add_user_message(validation.cleaned)
            conversation.add_assistant_message(full_answer, domain=final_domain)

            if user_id and long_term and profile:
                long_term.extract_and_remember(validation.cleaned, full_answer)
                profile.update_from_message(validation.cleaned, final_domain)

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            print(f"[Error] Streaming agent failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': 'Something went wrong. Please try again.'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable proxy buffering (nginx/Render)
        },
    )


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status":  "ok",
        "message": "Orrbit AI Agent is running 🚀",
    }


@app.get("/health")
def health():
    return {
        "status":   "healthy",
        "version":  "1.0.0",
        "features": [
            "multi-domain routing",
            "RAG pipeline",
            "web search",
            "conversation memory",
            "long-term memory",
            "user profiles",
            "authentication",
        ],
    }
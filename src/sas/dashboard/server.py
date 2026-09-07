"""Sovereign Agent Stack — Web Dashboard.

FastAPI backend with SSE streaming for live pipeline progress.
Single-page vanilla JS frontend.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

app = FastAPI(title="Sovereign Agent Stack", version="1.0.0")

# ── State ──────────────────────────────────────────────────────────────────────

# Module-level run state (one run at a time)
_run_active = False
_run_lock = asyncio.Lock()

# SSE subscribers
_sse_subscribers: list[asyncio.Queue] = []
_sse_loop: asyncio.AbstractEventLoop | None = None

# ── Static files ───────────────────────────────────────────────────────────────

STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)


def _notify_sse(data: dict) -> None:
    """Broadcast an event to all SSE subscribers."""
    global _sse_loop
    if _sse_loop is None:
        return
    for q in _sse_subscribers:
        try:
            _sse_loop.call_soon_threadsafe(q.put_nowait, data)
        except Exception:
            pass


# ── API Routes ─────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health() -> dict:
    """Health check."""
    return {
        "status": "ok",
        "timestamp": time.time(),
        "run_active": _run_active,
    }


@app.get("/api/layers")
async def layers() -> dict:
    """Get sovereignty layer scores."""
    try:
        from sas.core.config import SASConfig, parse_sas_yaml
        from sas.core.scoring import generate_report

        # Try to load from example config
        config_path = Path(__file__).resolve().parent.parent.parent / "examples" / "agency-worker" / "sas.yaml"
        if config_path.exists():
            config = parse_sas_yaml(config_path)
        else:
            config = SASConfig()

        report = generate_report(config)
        return {
            "score": report.score,
            "verdict": report.verdict,
            "owned": report.owned_count,
            "total": report.total_count,
            "layers": [
                {"name": l.name, "status": l.scored_as.value, "reasoning": l.reasoning}
                for l in report.layers
            ],
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/worlds")
async def worlds() -> dict:
    """List available quant worlds."""
    try:
        from sas.quant.worlds import (
            ADVERSTIONAL_WORLDS,
            MOMENTUM_WORLD,
            PORTFOLIO_INTELLIGENCE_WORLD,
            RISK_PARITY_WORLD,
        )

        world_list = [
            {
                "id": PORTFOLIO_INTELLIGENCE_WORLD.id,
                "customer": PORTFOLIO_INTELLIGENCE_WORLD.customer,
                "objective": PORTFOLIO_INTELLIGENCE_WORLD.objective,
                "universe": list(PORTFOLIO_INTELLIGENCE_WORLD.universe),
                "difficulty": PORTFOLIO_INTELLIGENCE_WORLD.difficulty,
                "estimated_minutes": PORTFOLIO_INTELLIGENCE_WORLD.estimated_human_minutes,
            },
            {
                "id": RISK_PARITY_WORLD.id,
                "customer": RISK_PARITY_WORLD.customer,
                "objective": RISK_PARITY_WORLD.objective,
                "universe": list(RISK_PARITY_WORLD.universe),
                "difficulty": RISK_PARITY_WORLD.difficulty,
                "estimated_minutes": RISK_PARITY_WORLD.estimated_human_minutes,
            },
            {
                "id": MOMENTUM_WORLD.id,
                "customer": MOMENTUM_WORLD.customer,
                "objective": MOMENTUM_WORLD.objective,
                "universe": list(MOMENTUM_WORLD.universe),
                "difficulty": MOMENTUM_WORLD.difficulty,
                "estimated_minutes": MOMENTUM_WORLD.estimated_human_minutes,
            },
        ]

        for name, wd in ADVERSTIONAL_WORLDS.items():
            world_list.append({
                "id": wd["world"].id,
                "customer": wd["world"].customer,
                "objective": wd["world"].objective,
                "universe": list(wd["world"].universe),
                "difficulty": wd["world"].difficulty,
                "estimated_minutes": wd["world"].estimated_human_minutes,
                "adversarial": True,
                "trap_type": wd["world"].metadata.get("trap_type", name),
            })

        return {"worlds": world_list}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/pipeline/run")
async def pipeline_run(request: Request) -> JSONResponse:
    """Start a pipeline run. Returns immediately; progress via SSE."""
    global _run_active

    body = await request.json()
    world_id = body.get("world_id", "qw-portfolio-intel-001")

    async with _run_lock:
        if _run_active:
            return JSONResponse({"error": "A run is already active"}, status_code=409)
        _run_active = True

    run_id = str(uuid.uuid4())[:8]

    # Start the run in the background
    asyncio.create_task(_run_pipeline(run_id, world_id))

    return JSONResponse({"accepted": True, "run_id": run_id})


async def _run_pipeline(run_id: str, world_id: str) -> None:
    """Run the pipeline in a thread and broadcast progress via SSE."""
    global _run_active

    def _emit(stage: str, message: str, data: dict | None = None):
        _notify_sse({
            "type": "progress",
            "run_id": run_id,
            "stage": stage,
            "message": message,
            "data": data or {},
            "timestamp": time.time(),
        })

    try:
        _emit("start", f"Starting pipeline run for world {run_id}")

        # Import here to avoid blocking the event loop
        await asyncio.to_thread(_sync_pipeline_run, run_id, world_id, _emit)

        _emit("complete", "Pipeline run complete", {"status": "completed"})

    except Exception as e:
        _emit("error", f"Pipeline failed: {e!s}", {"error": str(e)})
    finally:
        _run_active = False


def _sync_pipeline_run(run_id: str, world_id: str, emit) -> None:
    """Synchronous pipeline run (runs in a thread)."""
    from sas.quant.worlds import (
        MOMENTUM_RUBRIC,
        MOMENTUM_TASK,
        MOMENTUM_WORLD,
        PORTFOLIO_INTELLIGENCE_RUBRIC,
        PORTFOLIO_INTELLIGENCE_TASK,
        PORTFOLIO_INTELLIGENCE_WORLD,
        RISK_PARITY_RUBRIC,
        RISK_PARITY_TASK,
        RISK_PARITY_WORLD,
    )
    from tests.integration.test_quant_pipeline import (
        create_momentum_script,
        create_portfolio_intelligence_script,
        create_risk_parity_script,
        run_pipeline,
    )

    # Select world
    world_map = {
        PORTFOLIO_INTELLIGENCE_WORLD.id: (PORTFOLIO_INTELLIGENCE_WORLD, PORTFOLIO_INTELLIGENCE_TASK, PORTFOLIO_INTELLIGENCE_RUBRIC, create_portfolio_intelligence_script),
        RISK_PARITY_WORLD.id: (RISK_PARITY_WORLD, RISK_PARITY_TASK, RISK_PARITY_RUBRIC, create_risk_parity_script),
        MOMENTUM_WORLD.id: (MOMENTUM_WORLD, MOMENTUM_TASK, MOMENTUM_RUBRIC, create_momentum_script),
    }

    if world_id not in world_map:
        emit("error", f"Unknown world: {world_id}")
        return

    world, task, rubric, script_fn = world_map[world_id]

    emit("world", f"Loading world: {world.customer}", {"world_id": world.id})
    emit("task", f"Task: {task.prompt[:100]}...", {"task_id": task.id})

    # Run the pipeline
    emit("pipeline", "Running pipeline...")
    result = run_pipeline(world, task, rubric, script_fn())

    emit("evaluation", f"Evaluation complete. Pass@1: {result['benchmark']['pass_at_1']:.2f}", {
        "pass_at_1": result["benchmark"]["pass_at_1"],
        "mean_score": result["evaluation"]["mean_score"],
        "passed": result["evaluation"]["passed"],
        "sovereignty_passed": result["evaluation"]["sovereignty_passed"],
        "criterion_results": result["evaluation"]["criterion_results"],
        "artifacts": result["artifacts_created"],
        "tool_calls": result["tool_calls"],
    })


@app.get("/api/pipeline/stream")
async def pipeline_stream(request: Request) -> EventSourceResponse:
    """SSE endpoint for live pipeline progress."""
    global _sse_loop
    _sse_loop = asyncio.get_running_loop()

    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _sse_subscribers.append(queue)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30)
                    yield {"event": "message", "data": json.dumps(data)}
                except TimeoutError:
                    # Send keepalive
                    yield {"event": "keepalive", "data": "{}"}
        finally:
            if queue in _sse_subscribers:
                _sse_subscribers.remove(queue)

    return EventSourceResponse(event_generator())


@app.get("/api/knowledge")
async def knowledge(query: str = "", limit: int = 10) -> dict:
    """Query the knowledge graph."""
    try:
        from pathlib import Path

        from sas.layers.knowledge_resolver import compile_source, resolve_knowledge_backend

        store_path = ":memory:"
        adapter, kind = resolve_knowledge_backend(store_path=store_path)

        # Try to compile from a knowledge directory
        knowledge_dir = Path(__file__).resolve().parent.parent.parent / "knowledge"
        if knowledge_dir.exists():
            graph = compile_source(adapter, knowledge_dir)
        else:
            graph = adapter.load()

        if query:
            results = adapter.query(graph, query)
        else:
            results = graph.nodes[:limit] if hasattr(graph, "nodes") else []

        return {
            "query": query,
            "backend": kind,
            "results": [
                {"label": r.label, "content": r.properties.get("content", "")[:200]}
                for r in results[:limit]
            ],
            "count": len(results) if hasattr(results, "__len__") else 0,
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/agent/chat")
async def agent_chat(request: Request) -> JSONResponse:
    """Chat with the agent runtime."""
    try:
        body = await request.json()
        message = body.get("message", "")
        session_id = body.get("session_id", None)

        from sas.layers.memory_providers import InMemoryMemory
        from sas.layers.model_providers import StubModelProvider
        from sas.runtime.agent_runtime import AgentRuntime

        model = StubModelProvider(response="I am a sovereign AI assistant. How can I help you?")
        memory = InMemoryMemory()
        runtime = AgentRuntime(model=model, memory=memory)

        if session_id is None:
            session_id = await runtime.create_session("web-user")

        response = await runtime.run(session_id, message)

        return JSONResponse({
            "response": response,
            "session_id": session_id,
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ── Static file serving ───────────────────────────────────────────────────────

@app.get("/")
async def index() -> FileResponse:
    """Serve the main dashboard page."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse({"error": "Frontend not built"}, status_code=404)


# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "sas.dashboard.server:app",
        host="127.0.0.1",
        port=8080,
        reload=False,
        log_level="info",
    )

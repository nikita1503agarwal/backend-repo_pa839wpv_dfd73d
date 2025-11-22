import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Mindmap, MindmapNode

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Mindmap API ready"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Re-check envs
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# ---------------- Mindmap Endpoints ----------------

class MindmapCreate(BaseModel):
    title: str

class MindmapSave(BaseModel):
    title: str
    nodes: List[MindmapNode]

@app.post("/api/mindmaps", response_model=dict)
def create_mindmap(payload: MindmapCreate):
    try:
        mindmap = Mindmap(title=payload.title, nodes=[])
        inserted_id = create_document("mindmap", mindmap)
        return {"id": inserted_id, "title": mindmap.title, "nodes": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mindmaps", response_model=List[dict])
def list_mindmaps():
    try:
        docs = get_documents("mindmap")
        results = []
        for d in docs:
            results.append({
                "id": str(d.get("_id")),
                "title": d.get("title", "Untitled"),
                "nodes": d.get("nodes", [])
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mindmaps/{mindmap_id}", response_model=dict)
def get_mindmap(mindmap_id: str):
    try:
        doc = db["mindmap"].find_one({"_id": ObjectId(mindmap_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Mindmap not found")
        return {"id": str(doc["_id"]), "title": doc.get("title", "Untitled"), "nodes": doc.get("nodes", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/mindmaps/{mindmap_id}", response_model=dict)
def save_mindmap(mindmap_id: str, payload: MindmapSave):
    try:
        # Validate structure with schema
        _ = Mindmap(title=payload.title, nodes=payload.nodes)
        res = db["mindmap"].update_one(
            {"_id": ObjectId(mindmap_id)},
            {"$set": {"title": payload.title, "nodes": [n.model_dump() if hasattr(n, 'model_dump') else dict(n) for n in payload.nodes], "updated_at": None}}
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Mindmap not found")
        doc = db["mindmap"].find_one({"_id": ObjectId(mindmap_id)})
        return {"id": str(doc["_id"]), "title": doc.get("title", "Untitled"), "nodes": doc.get("nodes", [])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

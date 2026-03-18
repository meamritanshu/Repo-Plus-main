from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

# ✅ Relative import (FIXED)
from .repo_tools import (
    list_repo_files,
    read_file,
    apply_patch,
    commit_changes,
    revert_commit
)

app = FastAPI(title="AI Repo Tools API")

# ==============================
# ✅ Request Models
# ==============================

class PatchRequest(BaseModel):
    path: str
    patch: str

class CommitRequest(BaseModel):
    message: str

class ReadFileRequest(BaseModel):
    path: str


# ==============================
# ✅ Root Route (Fix for Not Found)
# ==============================

@app.get("/")
def home():
    return {"message": "AI Repo Tools API is running 🚀"}


# ==============================
# 📂 List Files in Repo
# ==============================

@app.get("/files", response_model=List[str])
def get_files():
    try:
        return list_repo_files()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================
# 📄 Read File Content
# ==============================

@app.post("/read-file")
def get_file_content(request: ReadFileRequest):
    try:
        content = read_file(request.path)
        return {"path": request.path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================
# 🛠 Apply Patch to File
# ==============================

@app.post("/apply-patch")
def patch_file(request: PatchRequest):
    try:
        result = apply_patch(request.path, request.patch)
        return {"status": "success", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================
# 💾 Commit Changes
# ==============================

@app.post("/commit")
def commit_repo(request: CommitRequest):
    try:
        result = commit_changes(request.message)
        return {"status": "committed", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================
# 🔙 Revert Last Commit
# ==============================

@app.post("/revert")
def revert_last_commit():
    try:
        result = revert_commit()
        return {"status": "reverted", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

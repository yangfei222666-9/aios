"""
Write MCP Server - 文件操作服务
支持读写本地文件
"""
import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Write MCP Server")

# 安全：限制操作目录
WORKSPACE_DIR = Path(__file__).parent.parent / "workspace"
WORKSPACE_DIR.mkdir(exist_ok=True)


class WriteRequest(BaseModel):
    filename: str
    content: str


class ReadRequest(BaseModel):
    filename: str


class FileResponse(BaseModel):
    filename: str
    content: Optional[str] = None
    size: Optional[int] = None
    success: bool
    message: str


def safe_path(filename: str) -> Path:
    """确保路径在 workspace 内"""
    path = (WORKSPACE_DIR / filename).resolve()
    if not str(path).startswith(str(WORKSPACE_DIR.resolve())):
        raise ValueError("Path traversal detected")
    return path


@app.get("/")
def root():
    return {
        "name": "Write MCP Server",
        "version": "1.0.0",
        "protocol": "MCP",
        "capabilities": ["file_read", "file_write", "file_list"],
        "workspace": str(WORKSPACE_DIR)
    }


@app.post("/write", response_model=FileResponse)
def write_file(request: WriteRequest) -> FileResponse:
    """写入文件"""
    try:
        path = safe_path(request.filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        path.write_text(request.content, encoding="utf-8")
        
        return FileResponse(
            filename=request.filename,
            size=len(request.content),
            success=True,
            message=f"File written: {request.filename}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/read", response_model=FileResponse)
def read_file(request: ReadRequest) -> FileResponse:
    """读取文件"""
    try:
        path = safe_path(request.filename)
        
        if not path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        content = path.read_text(encoding="utf-8")
        
        return FileResponse(
            filename=request.filename,
            content=content,
            size=len(content),
            success=True,
            message=f"File read: {request.filename}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/list")
def list_files():
    """列出所有文件"""
    try:
        files = []
        for path in WORKSPACE_DIR.rglob("*"):
            if path.is_file():
                rel_path = path.relative_to(WORKSPACE_DIR)
                files.append({
                    "filename": str(rel_path),
                    "size": path.stat().st_size,
                    "modified": path.stat().st_mtime
                })
        
        return {"files": files, "count": len(files)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "workspace": str(WORKSPACE_DIR),
        "writable": os.access(WORKSPACE_DIR, os.W_OK)
    }


if __name__ == "__main__":
    import uvicorn
    print(f"📝 Write MCP Server starting on http://localhost:8002")
    print(f"   Workspace: {WORKSPACE_DIR}")
    uvicorn.run(app, host="0.0.0.0", port=8002)

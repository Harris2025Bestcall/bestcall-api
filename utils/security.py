import os
from fastapi import Request, HTTPException, Depends

def verify_key(request: Request):
    expected_key = os.getenv("API_SECRET_KEY")
    provided_key = request.headers.get("x-api-key")

    if not expected_key or provided_key != expected_key:
        raise HTTPException(status_code=403, detail="Unauthorized")

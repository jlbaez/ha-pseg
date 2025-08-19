#!/usr/bin/env python3
"""PSEG Automation Addon - FastAPI Server"""

import asyncio
import logging
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from auto_login import get_fresh_cookies

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PSEG Automation", version="1.0.0")

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    cookies: Optional[str] = None
    error: Optional[str] = None

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "psegli-automation"}

@app.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login to PSEG and return cookies."""
    try:
        logger.info(f"Login attempt for user: {request.username}")
        
        # Get fresh cookies using the compatibility function
        cookies = await get_fresh_cookies(request.username, request.password)
        
        if cookies:
            logger.info("Login successful, cookies obtained")
            return LoginResponse(success=True, cookies=cookies)
        else:
            logger.warning("Login failed, no cookies returned")
            return LoginResponse(success=False, error="Login failed")
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return LoginResponse(success=False, error=str(e))

@app.post("/login-form", response_model=LoginResponse)
async def login_form(username: str = Form(...), password: str = Form(...)):
    """Login endpoint that accepts form data."""
    return await login(LoginRequest(username=username, password=password))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

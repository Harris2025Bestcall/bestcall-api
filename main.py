@app.post("/auth/login")
async def login(response: Response, email: str = Form(...), password: str = Form(...)):
    users = load_users()
    input_hash = hash_password(password)

    print("🔐 Attempting login for:", email)
    print("🔑 Hashed input password:", input_hash)

    for user in users:
        print("🧾 Stored user:", user["email"], "| Password hash:", user["password"])
        if user["email"] == email and user["password"] == input_hash:
            print("✅ Match found! Logging in:", email)
            session_id = hash_password(email)
            res = RedirectResponse(url="/client/dashboard", status_code=302)
            res.set_cookie(SESSION_COOKIE_NAME, session_id, httponly=True, max_age=3600)
            return res

    print("❌ Login failed for:", email)
    raise HTTPException(status_code=401, detail="Invalid login")

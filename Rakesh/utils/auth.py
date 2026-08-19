import hashlib
import json
from pathlib import Path
import streamlit as st

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "users.json"

DEFAULT_USERS = {
    "users": {}
}


def hash_password(password: str) -> str:
    """Compute SHA-256 hash of password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def load_users() -> dict:
    """Load users database from JSON file."""
    if not DATA_FILE.exists():
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_USERS, f, indent=2)
        return DEFAULT_USERS["users"]
    
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("users", {})
    except Exception:
        return DEFAULT_USERS["users"]


def save_users(users: dict) -> None:
    """Save users dictionary to JSON file."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"users": users}, f, indent=2)


def authenticate(username_or_email: str, password: str):
    """Authenticate user with username/email and password."""
    users = load_users()
    identifier = username_or_email.strip().lower()
    pw_hash = hash_password(password)

    for user in users.values():
        if (user["username"].lower() == identifier or user.get("email", "").lower() == identifier):
            if user["password_hash"] == pw_hash:
                return user
    return None


def register_user(username: str, name: str, email: str, password: str, role: str, security_question: str = "", security_answer: str = ""):
    """Register a new user in the database."""
    users = load_users()
    u_key = username.strip().lower()
    
    if u_key in users:
        return False, "Username already exists. Please choose a different username."
    
    for u in users.values():
        if u.get("email", "").lower() == email.strip().lower():
            return False, "Email is already registered. Please login or use forgot password."
    
    new_user = {
        "username": username.strip(),
        "password_hash": hash_password(password),
        "name": name.strip(),
        "email": email.strip().lower(),
        "role": role.strip().lower(),
        "security_question": security_question.strip(),
        "security_answer": security_answer.strip().lower()
    }
    
    users[u_key] = new_user
    save_users(users)
    return True, "Account created successfully! You can now sign in."


def reset_password(username_or_email: str, secret_answer: str, new_password: str):
    """Reset user password using security answer verification."""
    users = load_users()
    identifier = username_or_email.strip().lower()

    target_key = None
    for key, user in users.items():
        if user["username"].lower() == identifier or user.get("email", "").lower() == identifier:
            target_key = key
            break

    if not target_key:
        return False, "User account not found."

    user = users[target_key]
    stored_answer = user.get("security_answer", "").strip().lower()
    
    if stored_answer and stored_answer != secret_answer.strip().lower():
        return False, "Security answer is incorrect."

    user["password_hash"] = hash_password(new_password)
    users[target_key] = user
    save_users(users)
    return True, "Password reset successfully! Please sign in with your new password."


def get_current_user():
    """Retrieve logged-in user details from session state."""
    return st.session_state.get("user")


def is_authenticated() -> bool:
    """Check if a session is currently active and authenticated."""
    return st.session_state.get("authenticated", False)


def logout():
    """Clear authentication session and rerun."""
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.rerun()


def render_user_sidebar():
    """Display logged-in user profile badge and logout action in sidebar."""
    user = get_current_user()
    if not user:
        return

    st.sidebar.markdown("---")
    role = user.get("role", "technician").upper()
    badge_class = "role-badge-admin" if role == "ADMIN" else "role-badge-tech"
    role_icon = "👑" if role == "ADMIN" else "🔧"

    st.sidebar.markdown(
        f"""
        <div class="user-profile-card">
            <div class="user-avatar">{user.get('name', 'User')[0].upper()}</div>
            <div class="user-info">
                <div class="user-name">{user.get('name', 'User')}</div>
                <div class="user-email">{user.get('email', '')}</div>
                <span class="role-badge {badge_class}">{role_icon} {role}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True, type="secondary"):
        logout()


def require_auth(current_page_file: str = ""):
    """Verify session is authenticated."""
    if not is_authenticated():
        st.stop()
    return True

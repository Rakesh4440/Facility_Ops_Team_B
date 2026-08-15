import streamlit as st
from utils.auth import authenticate, register_user, reset_password

def _title(title, subtitle):
    st.markdown(f"""
    <div style="text-align:center;margin-bottom:1.2rem">
        <div style="width:72px;height:72px;margin:auto;border-radius:18px;
        display:flex;align-items:center;justify-content:center;
        background:linear-gradient(135deg,#2563eb,#06b6d4);
        color:white;font-size:34px;">🏢</div>
        <h2 style="margin-top:16px">{title}</h2>
        <p style="color:#94a3b8">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def render_auth_page():
    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"]="login"

    mode=st.session_state["auth_mode"]
    _,col,_=st.columns([1,2,1])

    with col:
        if mode=="login":
            _title("FacilityOps Login","Predictive Industrial Maintenance Platform")
            with st.form("login"):
                u=st.text_input("Username or Email")
                p=st.text_input("Password",type="password")
                if st.form_submit_button("Log in",use_container_width=True):
                    if not u or not p:
                        st.error("Please fill in all fields.")
                    else:
                        user=authenticate(u,p)
                        if user:
                            st.session_state["authenticated"]=True
                            st.session_state["user"]=user
                            st.rerun()
                        else:
                            st.error("Invalid username/email or password.")
            c1,c2=st.columns(2)
            with c1:
                if st.button("Create Account",use_container_width=True):
                    st.session_state["auth_mode"]="signup";st.rerun()
            with c2:
                if st.button("Forgot Password",use_container_width=True):
                    st.session_state["auth_mode"]="forgot";st.rerun()

        elif mode=="signup":
            _title("Create Account","Register as Admin or Technician")
            with st.form("signup"):
                name=st.text_input("Full Name")
                user=st.text_input("Username")
                email=st.text_input("Email")
                role=st.selectbox("Role",["admin","technician"])
                pwd=st.text_input("Password",type="password")
                cpwd=st.text_input("Confirm Password",type="password")
                q=st.selectbox("Security Question",[
                    "What is the primary facility location?",
                    "What is your technician badge number?",
                    "What is your favorite machine model?"
                ])
                a=st.text_input("Security Answer")
                if st.form_submit_button("Create Account",use_container_width=True):
                    if pwd!=cpwd:
                        st.error("Passwords do not match.")
                    else:
                        ok,msg=register_user(user,name,email,pwd,role,q,a)
                        if ok:
                            st.success(msg)
                            st.session_state["auth_mode"]="login";st.rerun()
                        else:
                            st.error(msg)
            if st.button("Back to Login",use_container_width=True):
                st.session_state["auth_mode"]="login";st.rerun()

        else:
            _title("Reset Password","Verify your security answer")
            with st.form("forgot"):
                u=st.text_input("Username or Email")
                a=st.text_input("Security Answer")
                np=st.text_input("New Password",type="password")
                cp=st.text_input("Confirm New Password",type="password")
                if st.form_submit_button("Reset Password",use_container_width=True):
                    if np!=cp:
                        st.error("Passwords do not match.")
                    else:
                        ok,msg=reset_password(u,a,np)
                        if ok:
                            st.success(msg)
                            st.session_state["auth_mode"]="login";st.rerun()
                        else:
                            st.error(msg)
            if st.button("Back to Login",use_container_width=True):
                st.session_state["auth_mode"]="login";st.rerun()

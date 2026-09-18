import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import base64
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="FinSight | FinSolve",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# BACKGROUND
# ============================================================

def set_background(image_path):
    """
    Loads the local background image and applies it
    to the complete Streamlit application.
    """

    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(
                image_file.read()
            ).decode()

        st.markdown(
            f"""
<style>
.stApp {{
    background-image:
        linear-gradient(
            rgba(3, 15, 29, 0.82),
            rgba(3, 15, 29, 0.90)
        ),
        url("data:image/jpeg;base64,{encoded}");

    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}
</style>
""",
            unsafe_allow_html=True
        )

    except FileNotFoundError:

        # Fallback background if image does not exist.
        st.markdown(
            """
<style>
.stApp {
    background:
        radial-gradient(
            circle at 80% 10%,
            #17486a 0%,
            #0b2942 28%,
            #061625 65%,
            #020a12 100%
        );

    background-attachment: fixed;
}
</style>
""",
            unsafe_allow_html=True
        )


# Resolve project root from ui.py location.
BASE_DIR = Path(__file__).resolve().parent

BACKGROUND_PATH = (
    BASE_DIR
    / "static"
    / "images"
    / "background.jpg"
)

set_background(BACKGROUND_PATH)


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown(
    """
<style>

/* =========================================================
   APPLICATION
   ========================================================= */

.block-container {
    max-width: 1450px;
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}


/* =========================================================
   HIDE STREAMLIT DEFAULT ELEMENTS
   ========================================================= */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    background: transparent !important;
}


/* =========================================================
   SIDEBAR
   ========================================================= */

[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            rgba(4, 21, 37, 0.98),
            rgba(2, 12, 23, 0.98)
        );

    border-right: 1px solid rgba(255,255,255,0.08);
}


/* =========================================================
   BRAND HEADER
   ========================================================= */

.brand-container {
    background:
        linear-gradient(
            135deg,
            rgba(7, 31, 53, 0.97),
            rgba(8, 61, 79, 0.94)
        );

    border: 1px solid rgba(255,255,255,0.12);

    border-radius: 18px;

    padding: 22px 28px;

    margin-bottom: 22px;

    box-shadow:
        0 18px 50px rgba(0,0,0,0.32);

    backdrop-filter: blur(14px);
}

.brand-name {
    font-size: 31px;

    font-weight: 800;

    color: #ffffff;

    letter-spacing: 0.4px;

    margin-bottom: 4px;
}

.brand-subtitle {
    font-size: 14px;

    color: #b9d0df;

    margin-bottom: 10px;
}

.brand-badge {
    display: inline-block;

    background:
        rgba(99,230,190,0.12);

    color: #63e6be;

    border:
        1px solid rgba(99,230,190,0.28);

    padding: 6px 12px;

    border-radius: 20px;

    font-size: 12px;

    font-weight: 600;
}


/* =========================================================
   GLASS CARD
   ========================================================= */

.glass-card {
    background:
        rgba(255,255,255,0.94);

    border:
        1px solid rgba(255,255,255,0.65);

    border-radius: 18px;

    padding: 24px;

    box-shadow:
        0 15px 45px rgba(0,0,0,0.20);

    backdrop-filter: blur(12px);
}


/* =========================================================
   LOGIN CARD
   ========================================================= */

.login-card {
    background:
        rgba(255,255,255,0.96);

    border-radius: 22px;

    padding: 30px;

    box-shadow:
        0 20px 60px rgba(0,0,0,0.35);

    border:
        1px solid rgba(255,255,255,0.70);

    margin-bottom: 15px;
}

.login-title {
    text-align: center;

    color: #09263d;

    font-size: 29px;

    font-weight: 800;

    margin-bottom: 6px;
}

.login-subtitle {
    text-align: center;

    color: #607d8b;

    font-size: 13px;

    line-height: 1.5;
}


/* =========================================================
   SECTION TITLES
   ========================================================= */

.section-title {
    color: #09263d;

    font-size: 22px;

    font-weight: 800;

    margin-bottom: 5px;
}

.section-description {
    color: #607d8b;

    font-size: 13px;

    line-height: 1.6;
}


/* =========================================================
   PROFILE
   ========================================================= */

.profile-card {
    background:
        rgba(6,25,43,0.92);

    border:
        1px solid rgba(255,255,255,0.10);

    border-radius: 15px;

    padding: 17px;

    margin-bottom: 16px;

    box-shadow:
        0 10px 30px rgba(0,0,0,0.25);
}

.profile-label {
    color: #8faec3;

    font-size: 10px;

    text-transform: uppercase;

    letter-spacing: 1px;

    margin-bottom: 3px;
}

.profile-value {
    color: #ffffff;

    font-size: 16px;

    font-weight: 700;

    margin-bottom: 12px;
}

.role-badge {
    display: inline-block;

    background:
        rgba(99,230,190,0.13);

    color: #63e6be;

    border:
        1px solid rgba(99,230,190,0.22);

    padding: 5px 10px;

    border-radius: 12px;

    font-size: 12px;

    font-weight: 700;
}


/* =========================================================
   INFORMATION CARDS
   ========================================================= */

.info-card {
    background:
        linear-gradient(
            145deg,
            rgba(7,31,51,0.96),
            rgba(8,46,66,0.92)
        );

    border:
        1px solid rgba(255,255,255,0.10);

    border-radius: 15px;

    padding: 19px;

    min-height: 125px;

    color: white;

    box-shadow:
        0 10px 30px rgba(0,0,0,0.20);
}

.info-card-title {
    font-size: 16px;

    font-weight: 700;

    margin-bottom: 8px;
}

.info-card-text {
    font-size: 12px;

    color: #a9c1d1;

    line-height: 1.6;
}


/* =========================================================
   ANSWER
   ========================================================= */

.answer-header {
    background:
        linear-gradient(
            135deg,
            #0b3554,
            #126e6a
        );

    color: white;

    padding: 13px 18px;

    border-radius: 12px 12px 0 0;

    font-weight: 700;

    margin-top: 20px;
}

.answer-box {
    background:
        rgba(255,255,255,0.97);

    color: #17324d;

    padding: 20px;

    border-radius: 0 0 12px 12px;

    border:
        1px solid rgba(0,0,0,0.08);

    box-shadow:
        0 8px 25px rgba(0,0,0,0.15);

    line-height: 1.7;
}


/* =========================================================
   BUTTONS
   ========================================================= */

.stButton > button {
    border-radius: 10px;

    font-weight: 700;

    border: none;

    min-height: 42px;
}


/* =========================================================
   INPUTS
   ========================================================= */

.stTextInput input,
.stTextArea textarea {
    border-radius: 10px;
}


/* =========================================================
   FILE UPLOADER
   ========================================================= */

[data-testid="stFileUploader"] {
    background:
        rgba(255,255,255,0.70);

    border-radius: 12px;

    padding: 10px;
}


/* =========================================================
   TABS
   ========================================================= */

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px;

    padding: 8px 18px;

    font-weight: 600;
}


/* =========================================================
   FOOTER
   ========================================================= */

.footer {
    text-align: center;

    color: rgba(255,255,255,0.62);

    font-size: 11px;

    margin-top: 35px;

    padding: 15px;
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "auth" not in st.session_state:
    st.session_state.auth = None

if "username" not in st.session_state:
    st.session_state.username = None

if "role" not in st.session_state:
    st.session_state.role = None

if "page" not in st.session_state:
    st.session_state.page = "login"

if "roles" not in st.session_state:
    st.session_state.roles = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ============================================================
# API HELPERS
# ============================================================

def get_auth():
    """
    Returns HTTP Basic Auth using the currently
    logged-in user's credentials.
    """

    if not st.session_state.auth:
        return None

    return HTTPBasicAuth(
        st.session_state.auth[0],
        st.session_state.auth[1]
    )


def fetch_roles():
    """
    Gets available roles from FastAPI.
    """

    try:

        response = requests.get(
            f"{API_URL}/roles",
            auth=get_auth(),
            timeout=10
        )

        if response.status_code == 200:

            return response.json().get(
                "roles",
                []
            )

        return []

    except requests.RequestException:

        return []


def display_api_error(response):
    """
    Displays FastAPI errors in a readable way.
    """

    try:

        detail = response.json().get(
            "detail",
            "Something went wrong."
        )

    except Exception:

        detail = (
            "Server error. Please check "
            "the FastAPI terminal."
        )

    st.error(f"❌ {detail}")


def logout():
    """
    Clears the current user's session.
    """

    st.session_state.auth = None

    st.session_state.username = None

    st.session_state.password = None

    st.session_state.role = None

    st.session_state.roles = []

    st.session_state.chat_history = []

    st.session_state.page = "login"


# ============================================================
# BRAND HEADER
# ============================================================

st.html(
    """
    <div class="brand-container">

        <div class="brand-name">
            💼 FinSight
        </div>

        <div class="brand-subtitle">
            Intelligent Data & Document Assistant
            for FinSolve Technologies
        </div>

        <div class="brand-badge">
            🔐 Role-Based Secure AI • RAG • Structured Data
        </div>

    </div>
    """
)


# ============================================================
# LOGIN PAGE
# ============================================================

if st.session_state.page == "login":

    # Empty columns are used to center the login card.
    left_space, login_col, right_space = st.columns(
        [1.2, 1, 1.2]
    )

    with login_col:

        st.html(
            """
            <div class="login-card">

                <div class="login-title">
                    Welcome to FinSight
                </div>

                <div class="login-subtitle">
                    Secure AI-powered knowledge assistant
                    for FinSolve Technologies
                </div>

            </div>
            """
        )

        username = st.text_input(
            "👤 Username",
            placeholder="Enter your username"
        )

        password = st.text_input(
            "🔑 Password",
            type="password",
            placeholder="Enter your password"
        )

        login_button = st.button(
            "🔐 Sign In",
            use_container_width=True
        )

        if login_button:

            if not username.strip():

                st.warning(
                    "Please enter your username."
                )

            elif not password:

                st.warning(
                    "Please enter your password."
                )

            else:

                try:

                    response = requests.get(
                        f"{API_URL}/login",
                        auth=HTTPBasicAuth(
                            username,
                            password
                        ),
                        timeout=10
                    )

                    if response.status_code == 200:

                        user_data = response.json()

                        # Store credentials for subsequent
                        # authenticated API requests.
                        st.session_state.auth = (
                            username,
                            password
                        )

                        st.session_state.username = username

                        st.session_state.password = password

                        st.session_state.role = user_data.get(
                            "role"
                        )

                        # Load roles after authentication.
                        st.session_state.roles = fetch_roles()

                        # Navigate to dashboard.
                        st.session_state.page = "main"

                        st.rerun()

                    else:

                        display_api_error(
                            response
                        )

                except requests.RequestException as error:

                    st.error(
                        f"❌ Cannot connect to FastAPI.\n\n{error}"
                    )


    # Login footer.
    st.html(
        """
        <div class="footer">

            <b>FinSight</b> • FinSolve Technologies<br>

            Secure Role-Based AI Knowledge Platform

        </div>
        """
    )


# ============================================================
# MAIN APPLICATION
# ============================================================

if st.session_state.page == "main":

    username = st.session_state.username

    role = st.session_state.role


    # ========================================================
    # SIDEBAR
    # ========================================================

    with st.sidebar:

        st.html(
            """
            <div style="
                text-align:center;
                padding:10px 0 20px 0;
            ">

                <div style="
                    font-size:42px;
                ">
                    💼
                </div>

                <div style="
                    color:white;
                    font-size:22px;
                    font-weight:800;
                ">
                    FinSight
                </div>

                <div style="
                    color:#91aec1;
                    font-size:11px;
                ">
                    FinSolve Technologies
                </div>

            </div>
            """
        )


        # User profile.
        st.html(
            f"""
            <div class="profile-card">

                <div class="profile-label">
                    Logged in as
                </div>

                <div class="profile-value">
                    👤 {username}
                </div>

                <div class="profile-label">
                    Access Role
                </div>

                <span class="role-badge">
                    🛡️ {role}
                </span>

            </div>
            """
        )


        # Security information.
        st.html(
            """
            <div class="info-card">

                <div class="info-card-title">
                    🔐 Secure Access
                </div>

                <div class="info-card-text">
                    Your permissions are enforced by
                    the FastAPI backend using
                    role-based access control.
                </div>

            </div>
            """
        )


        st.write("")


        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):

            logout()

            st.rerun()


    # ========================================================
    # DASHBOARD WELCOME
    # ========================================================

    st.html(
        f"""
        <div class="glass-card">

            <div class="section-title">
                Welcome back, {username} 👋
            </div>

            <div class="section-description">
                You are signed in with
                <b>{role}</b> access.
                Use FinSight to securely interact
                with authorized FinSolve Technologies
                documents and business data.
            </div>

        </div>
        """
    )


    st.write("")


    # ========================================================
    # ROLE-SPECIFIC TABS
    # ========================================================

    if role == "C-Level":

        tab1, tab2, tab3 = st.tabs(
            [
                "💬 AI Assistant",
                "📄 Document Management",
                "👤 Administration"
            ]
        )

    else:

        tab1 = st.tabs(
            [
                "💬 AI Assistant"
            ]
        )[0]


    # ========================================================
    # CHAT TAB
    # ========================================================

    with tab1:

        st.html(
            """
            <div class="glass-card">

                <div class="section-title">
                    🤖 FinSight AI Assistant
                </div>

                <div class="section-description">
                    Ask questions about authorized company
                    documents or structured business data.
                    FinSight determines whether the request
                    should use RAG or SQL-based retrieval.
                </div>

            </div>
            """
        )


        st.write("")


        # Three feature cards.
        card1, card2, card3 = st.columns(3)


        with card1:

            st.html(
                """
                <div class="info-card">

                    <div class="info-card-title">
                        📚 Document Intelligence
                    </div>

                    <div class="info-card-text">
                        Ask questions about policies,
                        reports, company information
                        and authorized documents.
                    </div>

                </div>
                """
            )


        with card2:

            st.html(
                """
                <div class="info-card">

                    <div class="info-card-title">
                        📊 Business Analytics
                    </div>

                    <div class="info-card-text">
                        Query structured CSV business
                        datasets using natural language
                        and SQL generation.
                    </div>

                </div>
                """
            )


        with card3:

            st.html(
                """
                <div class="info-card">

                    <div class="info-card-title">
                        🔐 RBAC Protection
                    </div>

                    <div class="info-card-text">
                        Retrieval and database access are
                        restricted according to the
                        authenticated user's role.
                    </div>

                </div>
                """
            )


        st.write("")
        st.write("")


        # ====================================================
        # QUESTION
        # ====================================================

        question = st.text_area(
            "Ask FinSight",
            placeholder=(
                "Example: What is the company's leave policy?\n"
                "Example: What was the total revenue last year?\n"
                "Example: Explain the uploaded finance report."
            ),
            height=120
        )


        submit_question = st.button(
            "🚀 Ask FinSight",
            use_container_width=True
        )


        if submit_question:

            if not question.strip():

                st.warning(
                    "Please enter a question first."
                )

            else:

                with st.spinner(
                    "FinSight is analyzing your question..."
                ):

                    try:

                        # The role is NOT sent from the frontend.
                        # FastAPI obtains the role from the
                        # authenticated user.
                        response = requests.post(
                            f"{API_URL}/chat",

                            json={
                                "question": question
                            },

                            auth=get_auth(),

                            timeout=120
                        )


                        if response.status_code == 200:

                            data = response.json()

                            answer = data.get(
                                "answer",
                                "No answer returned."
                            )


                            # Save conversation locally.
                            st.session_state.chat_history.append(
                                {
                                    "question": question,
                                    "answer": answer
                                }
                            )


                            st.html(
                                """
                                <div class="answer-header">
                                    🤖 FinSight Response
                                </div>
                                """
                            )


                            st.markdown(
                                f"""
                                <div class="answer-box">
                                    {answer}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )


                            # Show generated SQL when returned
                            # by the backend.
                            if data.get("sql"):

                                with st.expander(
                                    "🔎 View Generated SQL"
                                ):

                                    st.code(
                                        data["sql"],
                                        language="sql"
                                    )


                        else:

                            display_api_error(
                                response
                            )


                    except requests.Timeout:

                        st.error(
                            "⏱️ The AI request took too long. "
                            "Please try again."
                        )


                    except requests.RequestException as error:

                        st.error(
                            f"❌ FastAPI connection error: {error}"
                        )


        # ====================================================
        # CHAT HISTORY
        # ====================================================

        if st.session_state.chat_history:

            st.write("")

            st.subheader(
                "🕘 Recent Questions"
            )


            for index, chat in enumerate(
                reversed(
                    st.session_state.chat_history[-5:]
                ),
                start=1
            ):

                with st.expander(
                    f"Question {index}: {chat['question']}"
                ):

                    st.markdown(
                        chat["answer"]
                    )


            if st.button(
                "🗑️ Clear Chat History"
            ):

                st.session_state.chat_history = []

                st.rerun()


    # ========================================================
    # DOCUMENT MANAGEMENT
    # ========================================================

    if role == "C-Level":

        with tab2:

            st.html(
                """
                <div class="glass-card">

                    <div class="section-title">
                        📄 Document Management
                    </div>

                    <div class="section-description">
                        Upload CSV or Markdown documents and
                        assign the role that should be allowed
                        to retrieve them.
                    </div>

                </div>
                """
            )


            st.write("")


            # Refresh roles if required.
            if not st.session_state.roles:

                st.session_state.roles = fetch_roles()


            roles = st.session_state.roles


            if not roles:

                st.warning(
                    "No roles are currently available."
                )

            else:

                selected_role = st.selectbox(
                    "🛡️ Document Access Role",
                    roles,
                    key="document_role"
                )


                doc_file = st.file_uploader(
                    "📎 Select Document",
                    type=[
                        "csv",
                        "md"
                    ],
                    help=(
                        "Supported formats: CSV and Markdown."
                    ),
                    key="document_uploader"
                )


                if doc_file:

                    st.info(
                        f"Selected file: **{doc_file.name}**"
                    )


                upload_button = st.button(
                    "⬆️ Upload & Index Document",
                    use_container_width=True
                )


                if upload_button:

                    if doc_file is None:

                        st.warning(
                            "Please select a document first."
                        )

                    else:

                        with st.spinner(
                            "Uploading and indexing document..."
                        ):

                            try:

                                response = requests.post(
                                    f"{API_URL}/upload-docs",

                                    files={
                                        "file": (
                                            doc_file.name,
                                            doc_file.getvalue(),
                                            doc_file.type
                                        )
                                    },

                                    data={
                                        "role": selected_role
                                    },

                                    auth=get_auth(),

                                    timeout=180
                                )


                                if response.ok:

                                    data = response.json()

                                    st.success(
                                        data.get(
                                            "message",
                                            "Document uploaded successfully."
                                        )
                                    )

                                    st.info(
                                        "The document has been "
                                        "submitted for processing."
                                    )

                                else:

                                    display_api_error(
                                        response
                                    )


                            except requests.Timeout:

                                st.error(
                                    "⏱️ Upload timed out. "
                                    "Please check the FastAPI logs."
                                )


                            except requests.RequestException as error:

                                st.error(
                                    f"❌ Upload failed: {error}"
                                )


            st.write("")


            st.html(
                """
                <div class="info-card">

                    <div class="info-card-title">
                        💡 Document Security
                    </div>

                    <div class="info-card-text">
                        Each uploaded document is associated
                        with an access role. The backend is
                        responsible for enforcing authorization
                        during retrieval.
                    </div>

                </div>
                """
            )


    # ========================================================
    # ADMINISTRATION
    # ========================================================

    if role == "C-Level":

        with tab3:

            st.html(
                """
                <div class="glass-card">

                    <div class="section-title">
                        👤 Administration
                    </div>

                    <div class="section-description">
                        Manage FinSolve users and RBAC roles.
                        These operations are restricted to
                        C-Level users.
                    </div>

                </div>
                """
            )


            st.write("")


            # =================================================
            # CREATE USER
            # =================================================

            st.subheader(
                "➕ Create User"
            )


            admin_col1, admin_col2 = st.columns(2)


            with admin_col1:

                new_user = st.text_input(
                    "Username",
                    key="new_username",
                    placeholder="Enter new username"
                )


            with admin_col2:

                new_pass = st.text_input(
                    "Password",
                    type="password",
                    key="new_password",
                    placeholder="Enter temporary password"
                )


            roles = st.session_state.roles


            if roles:

                new_role = st.selectbox(
                    "Assign Role",
                    roles,
                    key="new_user_role"
                )

            else:

                new_role = None

                st.warning(
                    "Create a role before creating a user."
                )


            create_user_button = st.button(
                "👤 Create User",
                use_container_width=True
            )


            if create_user_button:

                if not new_user.strip():

                    st.warning(
                        "Username cannot be empty."
                    )

                elif not new_pass.strip():

                    st.warning(
                        "Password cannot be empty."
                    )

                elif not new_role:

                    st.warning(
                        "Please select a role."
                    )

                else:

                    try:

                        response = requests.post(
                            f"{API_URL}/create-user",

                            data={
                                "username": new_user,
                                "password": new_pass,
                                "role": new_role
                            },

                            auth=get_auth(),

                            timeout=20
                        )


                        if response.ok:

                            data = response.json()

                            st.success(
                                data.get(
                                    "message",
                                    "User created successfully."
                                )
                            )

                        else:

                            display_api_error(
                                response
                            )


                    except requests.RequestException as error:

                        st.error(
                            f"❌ Request failed: {error}"
                        )


            st.divider()


            # =================================================
            # CREATE ROLE
            # =================================================

            st.subheader(
                "🛡️ Create New Role"
            )


            new_role_input = st.text_input(
                "Role Name",
                key="new_role_name",
                placeholder="Example: Finance, HR, Legal"
            )


            create_role_button = st.button(
                "➕ Add Role",
                use_container_width=True
            )


            if create_role_button:

                if not new_role_input.strip():

                    st.warning(
                        "Role name cannot be empty."
                    )

                else:

                    try:

                        response = requests.post(
                            f"{API_URL}/create-role",

                            data={
                                "role_name": new_role_input
                            },

                            auth=get_auth(),

                            timeout=20
                        )


                        if response.ok:

                            data = response.json()

                            st.success(
                                data.get(
                                    "message",
                                    "Role created successfully."
                                )
                            )

                            # Refresh roles.
                            st.session_state.roles = fetch_roles()

                            st.rerun()

                        else:

                            display_api_error(
                                response
                            )


                    except requests.RequestException as error:

                        st.error(
                            f"❌ Request failed: {error}"
                        )


            st.divider()


            # =================================================
            # CURRENT ROLES
            # =================================================

            st.subheader(
                "📋 Available Roles"
            )


            current_roles = st.session_state.roles


            if current_roles:

                number_of_columns = min(
                    len(current_roles),
                    4
                )

                role_columns = st.columns(
                    number_of_columns
                )


                for index, current_role in enumerate(
                    current_roles
                ):

                    with role_columns[
                        index % number_of_columns
                    ]:

                        st.html(
                            f"""
                            <div class="info-card">

                                <div class="info-card-title">
                                    🛡️ {current_role}
                                </div>

                                <div class="info-card-text">
                                    Available RBAC role for
                                    users and documents.
                                </div>

                            </div>
                            """
                        )

            else:

                st.info(
                    "No roles found."
                )


    # ========================================================
    # FOOTER
    # ========================================================

    st.html(
        """
        <div class="footer">

            <b>FinSight</b> • FinSolve Technologies<br>

            Secure AI-Powered Enterprise Knowledge Platform
            • RBAC • RAG • SQL Analytics

        </div>
        """
    )
import os
from functools import wraps
from pathlib import Path
import unicodedata
from urllib.parse import urlsplit
from uuid import uuid4

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash

from .db import get_db, init_db


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
BINARY_SIGNATURES = (
    b"%PDF-",                    # PDF
    b"PK\x03\x04",               # ZIP and Office Open XML documents
    b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",  # Legacy Office documents
    b"\x89PNG\r\n\x1a\n",      # PNG
    b"\xff\xd8\xff",             # JPEG
    b"GIF87a",
    b"GIF89a",
    b"ID3",                      # MP3
    b"OggS",
)


def decode_material_text(content):
    if any(content.startswith(signature) for signature in BINARY_SIGNATURES):
        abort(400, description="只接受 TXT 或 Markdown 纯文本；不能只改扩展名来转换文件格式")
    try:
        if content.startswith((b"\xff\xfe", b"\xfe\xff")):
            text = content.decode("utf-16")
        else:
            try:
                text = content.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = content.decode("gb18030")
    except UnicodeDecodeError:
        abort(400, description="文件内容无法识别为支持的文本编码，请另存为 UTF-8、UTF-16 或 GB18030")
    if any(
        unicodedata.category(character) == "Cc" and character not in "\t\n\r\f"
        for character in text
    ):
        abort(400, description="文件包含非文本控制内容；目前只接受 TXT 或 Markdown 纯文本")
    return text


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        DATABASE=str(BASE_DIR / "data" / "app.db"),
        UPLOAD_FOLDER=str(UPLOAD_DIR),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SEED_TEACHER_PASSWORD=os.environ.get("SEED_TEACHER_PASSWORD"),
        SEED_STUDENT_A_PASSWORD=os.environ.get("SEED_STUDENT_A_PASSWORD"),
        SEED_STUDENT_B_PASSWORD=os.environ.get("SEED_STUDENT_B_PASSWORD"),
    )
    if test_config:
        app.config.update(test_config)
    if not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY environment variable is required")

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; "
            "form-action 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'",
        )
        response.headers.setdefault("Cache-Control", "no-store")
        return response

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    with app.app_context():
        init_db()

    def current_user():
        user_id = session.get("user_id")
        if not user_id:
            return None
        return get_db().execute(
            "SELECT id, username, role, class_id FROM users WHERE id = ?", (user_id,)
        ).fetchone()

    @app.context_processor
    def inject_user():
        return {"current_user": current_user()}

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user():
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)
        return wrapped

    def teacher_required(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user()["role"] != "teacher":
                abort(403)
            return view(*args, **kwargs)
        return wrapped

    def api_login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user():
                return jsonify(error="authentication_required"), 401
            return view(*args, **kwargs)
        return wrapped

    @app.get("/health")
    def health():
        get_db().execute("SELECT 1").fetchone()
        return {"status": "ok", "service": "campusclaw"}

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = get_db().execute(
                "SELECT id, username, password_hash, role, class_id FROM users WHERE username = ?",
                (username,),
            ).fetchone()
            if not user or not check_password_hash(user["password_hash"], password):
                flash("账号或密码不正确", "error")
            else:
                session.clear()
                session.update(user_id=user["id"], role=user["role"], class_id=user["class_id"])
                next_url = request.form.get("next", "").strip() or request.args.get("next", "")
                parsed_next = urlsplit(next_url)
                if (
                    parsed_next.netloc
                    or parsed_next.scheme
                    or not next_url.startswith("/")
                    or next_url.startswith("//")
                ):
                    next_url = url_for("dashboard")
                return redirect(next_url)
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    @login_required
    def dashboard():
        return redirect(url_for("materials"))

    @app.get("/materials")
    @login_required
    def materials():
        user = current_user()
        rows = get_db().execute(
            "SELECT id, title, filename, created_at FROM materials WHERE class_id = ? ORDER BY id DESC",
            (user["class_id"],),
        ).fetchall()
        return render_template("materials.html", materials=rows, user=user)

    @app.get("/api/knowledge/search")
    @api_login_required
    def search_knowledge():
        query = request.args.get("q", "").strip()
        if not query:
            return jsonify(query="", results=[])
        user = current_user()
        like_query = f"%{query}%"
        rows = get_db().execute(
            "SELECT m.id AS material_id, m.title, m.filename, k.content "
            "FROM knowledge_entries k JOIN materials m ON m.id = k.material_id "
            "WHERE k.class_id = ? AND m.class_id = ? "
            "AND (m.title LIKE ? OR m.filename LIKE ? OR k.content LIKE ?) "
            "ORDER BY k.created_at DESC, k.id DESC LIMIT 20",
            (user["class_id"], user["class_id"], like_query, like_query, like_query),
        ).fetchall()
        return jsonify(
            query=query,
            class_id=user["class_id"],
            results=[
                {
                    "material_id": row["material_id"],
                    "title": row["title"],
                    "source_filename": row["filename"],
                    "content": row["content"],
                }
                for row in rows
            ],
        )

    @app.post("/materials/upload")
    @teacher_required
    def upload_material():
        uploaded = request.files.get("file")
        if not uploaded or not uploaded.filename:
            flash("请选择 txt 或 md 文件", "error")
            return redirect(url_for("materials"))
        filename = Path(uploaded.filename.replace("\\", "/")).name
        if Path(filename).suffix.lower() not in {".txt", ".md"}:
            abort(400, description="只允许上传 .txt 或 .md 文件")
        content = uploaded.read()
        if not content:
            abort(400, description="文件不能为空")
        content_text = decode_material_text(content)
        user = current_user()
        db = get_db()
        target = None
        stored_file_created = False
        try:
            db.execute("BEGIN IMMEDIATE")
            existing_names = {
                row["filename"].casefold()
                for row in db.execute(
                    "SELECT filename FROM materials WHERE class_id = ?",
                    (user["class_id"],),
                ).fetchall()
            }
            display_filename = filename
            stem, extension = Path(filename).stem, Path(filename).suffix
            sequence = 1
            while display_filename.casefold() in existing_names:
                display_filename = f"{stem} ({sequence}){extension}"
                sequence += 1

            title = Path(display_filename).stem[:120]
            storage_name = f"{uuid4().hex}{extension.lower()}"
            target = Path(app.config["UPLOAD_FOLDER"]) / storage_name
            with target.open("xb") as stored_file:
                stored_file_created = True
                stored_file.write(content)
            cursor = db.execute(
                "INSERT INTO materials (class_id, uploader_id, title, filename, storage_name) VALUES (?, ?, ?, ?, ?)",
                (user["class_id"], user["id"], title, display_filename, storage_name),
            )
            db.execute(
                "INSERT INTO knowledge_entries (class_id, material_id, content) VALUES (?, ?, ?)",
                (user["class_id"], cursor.lastrowid, content_text),
            )
            db.commit()
        except Exception:
            db.rollback()
            if stored_file_created and target is not None:
                target.unlink(missing_ok=True)
            raise
        flash("材料已上传并进入本班知识库", "success")
        return redirect(url_for("materials"))

    @app.get("/materials/<int:material_id>")
    @login_required
    def material_detail(material_id):
        user = current_user()
        material = get_db().execute(
            "SELECT m.id, m.title, m.filename, k.content FROM materials m "
            "JOIN knowledge_entries k ON k.material_id = m.id "
            "WHERE m.id = ? AND m.class_id = ? AND k.class_id = ?",
            (material_id, user["class_id"], user["class_id"]),
        ).fetchone()
        if not material:
            abort(404)
        return render_template("material_detail.html", material=material)

    @app.get("/materials/<int:material_id>/download")
    @login_required
    def download_material(material_id):
        user = current_user()
        material = get_db().execute(
            "SELECT filename, storage_name FROM materials "
            "WHERE id = ? AND class_id = ?",
            (material_id, user["class_id"]),
        ).fetchone()
        if not material:
            abort(404)
        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            material["storage_name"],
            as_attachment=True,
            download_name=material["filename"],
        )

    @app.teardown_appcontext
    def close_db(_error=None):
        from .db import close_db as close
        close()

    return app


app = create_app() if os.environ.get("CAMPUSCLAW_SKIP_APP") != "1" else None

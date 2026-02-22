import os
from tinydb import TinyDB, Query

from app.core.config import settings

DB_PATH = os.path.join(settings.UPLOAD_DIR, "../data.json")
os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)

db = TinyDB(DB_PATH)
files_table = db.table("files")
chats_table = db.table("chat_sessions")
shares_table = db.table("shares")
File = Query()
Chat = Query()
Share = Query()

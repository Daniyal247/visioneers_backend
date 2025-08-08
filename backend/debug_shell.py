# debug_shell.py
from app.models.user import User
from app.core.database import SessionLocal

db = SessionLocal()

# Example query
users = db.query(User).all()
for user in users:
    print(user.id, user.email, user.username)

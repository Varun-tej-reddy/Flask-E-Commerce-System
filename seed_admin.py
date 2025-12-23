from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()
app.app_context().push()

admin = User.query.filter_by(username='dev@gmail.com').first()
if not admin:
    admin = User(
        username='dev@gmail.com',
        password=generate_password_hash('dev@1234', method='pbkdf2:sha256', salt_length=8),
        role='admin'
    )
    db.session.add(admin)
    db.session.commit()
    print("Admin user created.")
else:
    print("Admin already exists.")
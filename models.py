from app import db
from datetime import datetime
from flask_login import UserMixin

class User(UserMixin, db.Model):
    """Model for user authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

class Recipient(db.Model):
    """Model for storing message recipients"""
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(100), unique=True, nullable=False)  # телефон или @username
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Recipient {self.identifier}>'

class MessageLog(db.Model):
    """Model to store message sending logs"""
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False)
    recipient = db.Column(db.String(100), nullable=False)
    message_preview = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'success', 'failed', 'pending'
    error_message = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MessageLog {self.id}: {self.status} to {self.recipient}>'

class BroadcastSession(db.Model):
    """Model to store broadcast session information"""
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False)
    recipient_count = db.Column(db.Integer, nullable=False, default=0)
    successful_count = db.Column(db.Integer, nullable=False, default=0)
    failed_count = db.Column(db.Integer, nullable=False, default=0)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='in_progress')  # 'in_progress', 'completed', 'failed'

    def __repr__(self):
        return f'<BroadcastSession {self.id}: {self.status}, {self.successful_count}/{self.recipient_count}>'
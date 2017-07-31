import datetime

from app import app

from flask_bcrypt import Bcrypt

from flask_sqlalchemy import SQLAlchemy

from itsdangerous import TimedJSONWebSignatureSerializer, BadSignature, SignatureExpired

from sqlalchemy.ext.hybrid import hybrid_property


db = SQLAlchemy(app)
hashing = Bcrypt(app)


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    _password = db.Column(db.LargeBinary(), nullable=False)
    first_name = db.Column(db.String(30), nullable=True)
    last_name = db.Column(db.String(30), nullable=True)
    date_joined = db.Column(db.DateTime(), default=datetime.datetime.now())
    is_active = db.Column(db.Boolean(), default=True)
    last_login = db.Column(db.DateTime(), nullable=True)
    buckets = db.relationship("Bucket", backref='user', lazy='dynamic')
    activities = db.relationship("Activity", backref='user', lazy='dynamic')

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self._password = hashing.generate_password_hash(password)

    def check_password(self, password):
        return hashing.check_password_hash(self.password, password)

    @staticmethod
    def exists(email):
        user = User.query.filter_by(email=email).first()
        if user:
            return True
        else:
            return False

    def save(self):
        db.session.add(self)
        db.session.commit()
        return User.query.filter_by(email=self.email).first()

    @classmethod
    def drop_all(cls):
        try:
            db.session.query(cls).delete()
            db.session.commit()

        except Exception:
            db.session.rollback()

    def get_id(self):
        return self.user_id

    def generate_token(self):
        key = TimedJSONWebSignatureSerializer(app.config['SECRET_KEY'], expires_in=1800)
        return key.dumps(dict(id=self.id))

    @staticmethod
    def verify_token(token):
        key = TimedJSONWebSignatureSerializer(app.config['SECRET_KEY'])

        try:
            data = key.loads(token)

        except (SignatureExpired, BadSignature):
            return None
        return User.query.filter_by(id=data['id']).first()


class Bucket(db.Model):
    __tablename__ = 'bucket'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bucket_name = db.Column(db.String(70), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    created = db.Column(db.DateTime(), default=datetime.datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    description = db.Column(db.String(100), nullable=False)
    activities = db.relationship("Activity", backref='bucket', lazy='dynamic')

    def get_id(self):
        return self.bucket_id

    def save(self):
        db.session.add(self)
        db.session.commit()
        return Bucket.query.filter_by(id=self.id).first()


class Category(db.Model):
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_name = db.Column(db.String(70), nullable=False, unique=True)
    category = db.relationship(Bucket, backref='category', lazy='dynamic')

    def save(self):
        db.session.add(self)
        db.session.commit()
        return Category.query.filter_by(id=self.id).first()


class Activity(db.Model):
    __tablename__ = 'activity'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.Text())
    bucket_id = db.Column(db.Integer, db.ForeignKey('bucket.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def get_id(self):
        return self.id

    def save(self):
        db.session.add(self)
        db.session.commit()
        return Activity.query.filter_by(id=self.id).first()

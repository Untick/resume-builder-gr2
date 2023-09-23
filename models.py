from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool


# База данных
DATABASE_URL = "sqlite:///sqlite.db"
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)
SessionLocal = scoped_session(sessionmaker(autoflush=True, bind=engine))
Base = declarative_base()


# Пользователь
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(30), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    # связи:
    contacts = relationship(
        "Contact", back_populates="user", cascade="all, delete-orphan"
    )


class ContactType(Base):
    """Телефон, Email, github, LinkedIn, VK и прочие."""

    __tablename__ = "contact_types"
    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True, nullable=False)
    contacts = relationship(
        "Contact", back_populates="contact_type", cascade="all, delete-orphan"
    )


class Contact(Base):
    """Контакт пользователя."""

    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    text = Column(String(50), unique=True, nullable=False)
    is_show = Column(Boolean, default=True, nullable=False)

    contact_type_id = Column(Integer, ForeignKey("contact_types.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    # связи:
    contact_type = relationship("ContactType", back_populates="contacts")
    user = relationship("User", back_populates="contacts")


# Анкета пользователя
class AppForm(Base):
    __tablename__ = "appform"
    id = Column(Integer, ForeignKey(User.id), primary_key=True)
    skillPython = Column(Boolean)
    skillNumPy = Column(Boolean)
    skillPandas = Column(Boolean)
    skillMatplotlib = Column(Boolean)
    skillSeaborn = Column(Boolean)
    skillKeras = Column(Boolean)
    skillPytorch = Column(Boolean)
    skillTensorflow = Column(Boolean)
    skillNLP = Column(Boolean)
    skillGPT = Column(Boolean)
    skillObjectDetection = Column(Boolean)
    customSkills = Column(String)
    education = Column(String)
    experience = Column(String)
    courseDataScience = Column(Boolean)
    coursePython = Column(Boolean)


# Сгенерированное резюме
class Resume(Base):
    __tablename__ = "resume"
    id = Column(Integer, ForeignKey(User.id), primary_key=True)
    resume = Column(Text)

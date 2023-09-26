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


class User(Base):
    """Пользователь."""

    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(30), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    is_ready_to_relocate = Column(Boolean)
    city = Column(String(100))

    # связи:
    contacts = relationship(
        "Contact", back_populates="user", cascade="all, delete-orphan"
    )
    languages = relationship(
        "UserLanguage", back_populates="user", cascade="all, delete-orphan"
    )
    documents = relationship(
        "Document", back_populates="user", cascade="all, delete-orphan"
    )
    education = relationship(
        "Education", back_populates="user", cascade="all, delete-orphan"
    )


class Education(Base):
    """Образование, курсы."""

    __tablename__ = "education"
    id = Column(Integer, primary_key=True)
    text = Column(Text)
    started = Column(DateTime)
    finished = Column(DateTime)
    education_type = Column(String(25), nullable=False)  # Высшее, среднее, курсы
    institution = Column(String(100))  # Институт, организация
    faculty = Column(String(100))  # факультет, название курса
    is_show = Column(Boolean, default=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # связь
    user = relationship("User", back_populates="education")


class UserLanguage(Base):
    """Иностранный язык пользователя."""

    __tablename__ = "user_languages"
    id = Column(Integer, primary_key=True)
    language_name = Column(String(30), nullable=False)
    language_level = Column(String(30))
    is_show = Column(Boolean, default=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # связи:
    user = relationship("User", back_populates="languages")


class Contact(Base):
    """Контакт пользователя."""

    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    contact_text = Column(String(50), unique=True, nullable=False)
    is_show = Column(Boolean, default=True, nullable=False)
    contact_type = Column(String(20), nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # связи:
    user = relationship("User", back_populates="contacts")


# # Анкета пользователя
# class AppForm(Base):
#     __tablename__ = "appform"
#     id = Column(Integer, ForeignKey(User.id), primary_key=True)
#     skillPython = Column(Boolean)
#     skillNumPy = Column(Boolean)
#     skillPandas = Column(Boolean)
#     skillMatplotlib = Column(Boolean)
#     skillSeaborn = Column(Boolean)
#     skillKeras = Column(Boolean)
#     skillPytorch = Column(Boolean)
#     skillTensorflow = Column(Boolean)
#     skillNLP = Column(Boolean)
#     skillGPT = Column(Boolean)
#     skillObjectDetection = Column(Boolean)
#     customSkills = Column(String)
#     education = Column(String)
#     experience = Column(String)
#     courseDataScience = Column(Boolean)
#     coursePython = Column(Boolean)


# # Сгенерированное резюме
# class Resume(Base):
#     __tablename__ = "resume"
#     id = Column(Integer, ForeignKey(User.id), primary_key=True)
#     resume = Column(Text)


class Document(Base):
    """Документ: анкета, резюме, вакансия и пр."""

    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    status = Column(String(30), default="created")  #
    profession = Column(String(50))
    profession_level = Column(String(30))
    document_type = Column(String(10))
    html_template = Column(String(50))

    user = relationship(
        "User", back_populates="documents", cascade="all, delete-orphan"
    )
    document_skills = relationship(
        "DocumentSkill", back_populates="documents", cascade="all, delete-orphan"
    )
    sections = relationship(
        "Section", back_populates="document", cascade="all, delete-orphan"
    )
    experience = relationship(
        "Experience", back_populates="document", cascade="all, delete-orphan"
    )


class Experience(Base):
    """Опыт работы.

    Раздел "Опыт работы" всегда присутствует в документе.
    'text' - описание опыта работы пользователя в произвольной(нераспарсенной) форме.
    Компания, проект, профессия, обязанности, достижения, начала и окончание, \
    статус, обработано chatGPT.
    """

    __tablename__ = "experience"
    id = Column(Integer, primary_key=True)
    text = Column(Text)
    company = Column(String(100))
    city = Column(String(100))
    project = Column(String(100))
    profession = Column(String(100))
    experience_type = Column(
        String(100)
    )  # основная работа, фриланс, проектная деятельность, личный проект
    duties = Column(String(100))  # обязанности
    аchievements = Column(String(100))  # достижения
    started = Column(DateTime)
    finished = Column(DateTime)
    status = Column(String(30), default="unprocessed")  #
    gpt_parsed = Column(Boolean, default=False)
    document_id = Column(Integer, ForeignKey("documents.id"))

    # связи
    document = relationship("Document", back_populates="experience")


class Section(Base):
    """Секция (раздел) документа.
    
    Сюда относятся текстовые разделы, которые не являются обязательными:
    Хобби, хакатон, публикация, рекомендации от других людей, \
    "о себе", дополнительно и прочие.
    """

    __tablename__ = "sections"
    id = Column(Integer, primary_key=True)
    section_type = Column(String(50), nullable=False)
    text = Column(Text)
    status = Column(String(30), default="unprocessed")
    is_show = Column(Boolean, default=True, nullable=False)
    order_section = Column(Integer, default=5)
    document_id = Column(Integer, ForeignKey("documents.id"))

    # связь
    document = relationship("Document", back_populates="sections")


class Skill(Base):
    """Навыки (Справочник)."""

    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    skill_type = Column(String(100))  # hardskill or softskill or other..

    # связь
    document_skills = relationship(
        "DocumentSkill", back_populates="skills", cascade="all, delete-orphan"
    )


class DocumentSkill(Base):
    """Навыки в документе."""

    __tablename__ = "document_skills"
    # id = Column(Integer, primary_key=True)
    document_id = Column(
        Integer, ForeignKey("documents.id"), nullable=False, primary_key=True
    )
    skill_id = Column(
        Integer, ForeignKey("skills.id"), nullable=False, primary_key=True
    )
    is_show = Column(Boolean, default=True, nullable=False)
    order_skill = Column(Integer, default=5)

    # связь
    documents = relationship("Document", back_populates="document_skills")
    skills = relationship("Skill", back_populates="document_skills")

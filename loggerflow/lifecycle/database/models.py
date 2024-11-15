from sqlalchemy import Column, String, Integer, DATETIME, ForeignKey, TEXT, Enum, JSON, Boolean, Table
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm import relationship

from loggerflow.lifecycle.database import Base

from datetime import datetime
from typing import Optional

import enum


class Status(enum.Enum):
    online = "ONLINE"
    offline = "OFFLINE"


class Implementation(enum.Enum):
    webhook = "WEBHOOK"
    websocket = "WEBSOCKET"

class Event(enum.Enum):
    startup = "STARTUP"
    shutdown = "SHUTDOWN"


class UtilsMixin:

    def update_from_dict(self, data_dict):
        updated = False

        for key, value in data_dict.items():
            if hasattr(self, key):
                if getattr(self, key) != value:
                    setattr(self, key, value)
                    updated = True
                    flag_modified(self, key)

        return updated

class LFSettings(Base, UtilsMixin):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    show_first_clean_traceback = Column(Boolean, default=False)
    show_process_memory = Column(Boolean, default=False)
    # save_metrics = Column(Boolean, default=True)
    backlight_traceback = Column(Boolean, default=True)


    def __init__(self, show_first_clean_traceback: bool, show_process_memory: bool, backlight_traceback: bool):
        self.show_first_clean_traceback = show_first_clean_traceback
        self.show_process_memory = show_process_memory
        # self.save_metrics = save_metrics
        self.backlight_traceback = backlight_traceback

    def __str__(self):
        return f'Settings({self.id})'

    def to_dict(self):
        return {
            'id': self.id,
            'show_first_clean_traceback': self.show_first_clean_traceback,
            'show_process_memory': self.show_process_memory,
            # 'save_metrics': self.save_metrics,
            'backlight_traceback': self.backlight_traceback,
        }

project_alarmer_association = Table(
    'project_alarmer_association', Base.metadata,
    Column('project_id', Integer, ForeignKey('project.id', ondelete='CASCADE')),
    Column('alarmer_id', Integer, ForeignKey('alarms.id', ondelete='CASCADE')),
)


class Alarmer(Base):
    __tablename__ = "alarms"
    id = Column(Integer, primary_key=True, index=True)
    alarmer_name = Column(String, nullable=False)
    backend_type = Column(String, nullable=False)
    config_data = Column(JSON, nullable=False)
    projects = relationship(
        "Project",
        secondary=project_alarmer_association,
        back_populates="connected_alarms",
        passive_deletes=True
    )
    alarm_events = relationship(
        "AlarmEvent",
        back_populates="alarm",
        cascade="all, delete-orphan"
    )


    def __init__(self, alarmer_name, backend_type, config_data):
        self.alarmer_name = alarmer_name
        self.backend_type = backend_type
        self.config_data = config_data


    def __str__(self):
        return f'Alarm({self.backend_type})'

    def to_dict(self):
        return {
            'id': self.id,
            'alarmer_name': self.alarmer_name,
            'backend_type': self.backend_type,
        }


class Project(Base, UtilsMixin):
    __tablename__ = 'project'

    id = Column(Integer, primary_key=True)
    project_name = Column(String(255))
    status = Column(Enum(Status))
    heartbeat = Column(Integer)
    last_heartbeat = Column(DATETIME)
    last_readings = Column(JSON)
    authors = Column(String, nullable=True)
    connected_backends = Column(String)
    implementation = Column(Enum(Implementation))
    hidden = Column(Boolean, default=False)
    created_at = Column(DATETIME, default=datetime.now)
    exceptions = relationship('ProjectException', back_populates='project', cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="project", cascade="all, delete-orphan")

    connected_alarms = relationship(
        "Alarmer",
        secondary=project_alarmer_association,
        back_populates="projects",
        passive_deletes=True
    )
    alarm_events = relationship(
        "AlarmEvent",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    def __init__(self, project_name: str, status: Status,
                 heartbeat: int,
                 last_readings: str,
                 connected_backends: str,
                 implementation: Implementation,
                 last_heartbeat: datetime = datetime.now(),
                 authors: Optional[str] = None,
                 hidden: bool = False):

        self.project_name = project_name
        self.status = status
        self.heartbeat = heartbeat
        self.last_heartbeat = last_heartbeat
        self.last_readings = last_readings
        self.connected_backends = connected_backends
        self.implementation = implementation
        self.authors = authors
        self.hidden = hidden

    def __str__(self):
        return f"{self.project_name} - {self.status} - {self.last_heartbeat}"

    def to_dict(self):
        return {
            "id": self.id,
            "project_name": self.project_name,
            "status": self.status.value,
            "heartbeat": self.heartbeat,
            "last_heartbeat": self.last_heartbeat.strftime("%Y-%m-%d %H:%M:%S"),
            "last_readings": self.last_readings,
            "connected_backends": self.connected_backends,
            "implementation": self.implementation.value,
            "authors": self.authors,
            "hidden": self.hidden,
            "exceptions_count": self.exceptions_count if hasattr(self, 'exceptions_count') else 0
        }


class AlarmEvent(Base):
    __tablename__ = "alarm_events"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    alarm_id = Column(Integer, ForeignKey("alarms.id", ondelete="CASCADE"), nullable=True)
    event_type = Column(Enum(Event), nullable=False)
    event_time = Column(DATETIME, nullable=False, default=datetime.now)
    message = Column(String, nullable=True)

    project = relationship("Project", back_populates="alarm_events")
    alarm = relationship("Alarmer", back_populates="alarm_events")

    def __init__(self, project_id: int, alarm_id: int, event_type: Event, event_time: datetime, message: str = None):
        self.project_id = project_id
        self.alarm_id = alarm_id
        self.event_type = event_type
        self.event_time = event_time
        self.message = message

    def __str__(self):
        return f"AlarmEvent(Project ID: {self.project_id}, Alarm ID: {self.alarm_id}, Event: {self.event_type})"

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "alarm_id": self.alarm_id,
            "event_type": self.event_type,
            "event_time": self.event_time.strftime("%Y-%m-%d %H:%M:%S"),
            "message": self.message
        }


class Metric(Base):
    __tablename__ = "metrics"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    data = Column(JSON, nullable=False)
    last_heartbeat = Column(DATETIME, nullable=False, default=datetime.now)

    project = relationship("Project", back_populates="metrics")

    def __init__(self, project_id: int, data: dict, last_heartbeat: datetime):
        self.project_id = project_id
        self.data = data
        self.last_heartbeat = last_heartbeat

    def __str__(self):
        return f'Metric({self.project})'

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "data": self.data,
            "last_heartbeat": self.last_heartbeat.strftime("%Y-%m-%d %H:%M:%S"),
        }



class ProjectException(Base):
    __tablename__ = 'project_exception'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    traceback = Column(TEXT)
    error_date = Column(DATETIME, default=datetime.now)

    project = relationship('Project', back_populates='exceptions')

    def __init__(self, project_id: int, traceback: str):
        self.project_id = project_id
        self.traceback = traceback

    def __str__(self):
        return f'{self.project_id}'

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "traceback": self.traceback,
            "error_date": self.error_date,
        }

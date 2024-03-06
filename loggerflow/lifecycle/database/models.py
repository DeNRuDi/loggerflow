from sqlalchemy import Column, String, Integer, DATETIME, ForeignKey, TEXT, Enum, JSON, Boolean
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


class Project(Base):
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

    def update_from_dict(self, data_dict):
        updated = False

        for key, value in data_dict.items():
            if hasattr(self, key):
                if getattr(self, key) != value:
                    setattr(self, key, value)
                    updated = True
                    flag_modified(self, key)

        return updated

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

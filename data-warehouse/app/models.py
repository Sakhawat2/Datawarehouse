import uuid
import datetime as dt
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    BigInteger,
    Float,
    Index,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base


# ────────────────────────────────
# 👤 USER MODEL
# ────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(Text, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    # Relationships
    sensors = relationship("Sensor", back_populates="owner", cascade="all, delete-orphan")
    readings = relationship("SensorReading", back_populates="owner", cascade="all, delete-orphan")
    videos = relationship("VideoAsset", back_populates="owner", cascade="all, delete-orphan")
    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")  # ✅ added


# ────────────────────────────────
# 🌡 SENSOR MODEL
# ────────────────────────────────
class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    license = Column(Text, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="sensors")
    readings = relationship("SensorReading", back_populates="sensor", cascade="all, delete-orphan")


# ────────────────────────────────
# 📈 SENSOR READING MODEL
# ────────────────────────────────
class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sensor_id = Column(UUID(as_uuid=True), ForeignKey("sensors.id"), index=True)
    ts = Column(DateTime, nullable=False, index=True)
    ts_end = Column(DateTime, nullable=True)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    license = Column(Text, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    sensor = relationship("Sensor", back_populates="readings")
    owner = relationship("User", back_populates="readings")


# ✅ Index for efficient time-based querying
Index("ix_sr_sensor_ts", SensorReading.sensor_id, SensorReading.ts)


# ────────────────────────────────
# 🎥 VIDEO MODEL
# ────────────────────────────────
class VideoAsset(Base):
    __tablename__ = "video_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(Text, nullable=False)
    size_bytes = Column(BigInteger, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    license = Column(Text, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="videos")


# ────────────────────────────────
# 📁 FILE MODEL (SINGLE FINAL VERSION)
# ────────────────────────────────
class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    filetype = Column(String, nullable=True)
    size = Column(Float, nullable=True)  # size in MB
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="files")

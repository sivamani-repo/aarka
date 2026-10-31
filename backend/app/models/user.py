from sqlalchemy import (
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    func,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)


class Role(Base):
    __tablename__ = "roles"

    name = Column(String(80), primary_key=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    description = Column(String(255), nullable=False)
    department = relationship("Department")


class Permission(Base):
    __tablename__ = "permissions"

    resource = Column(String(80), primary_key=True)
    action = Column(String(20), primary_key=True)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_name = Column(String(80), ForeignKey("roles.name", ondelete="CASCADE"), primary_key=True)
    resource = Column(String(80), primary_key=True)
    action = Column(String(20), primary_key=True)
    __table_args__ = (
        ForeignKeyConstraint(
            ["resource", "action"],
            ["permissions.resource", "permissions.action"],
            ondelete="CASCADE",
        ),
    )


class UserPermission(Base):
    __tablename__ = "user_permissions"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    resource = Column(String(80), primary_key=True)
    action = Column(String(20), primary_key=True)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(
            ["resource", "action"],
            ["permissions.resource", "permissions.action"],
            ondelete="CASCADE",
        ),
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for Google-only authentication
    role = Column(String(80), nullable=False, default="Customer")
    phone = Column(String(30), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    employee_id = Column(String(32), unique=True, nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    reporting_manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    google_sub = Column(String(255), unique=True, nullable=True, index=True)
    verification_token = Column(String(255), nullable=True, index=True)
    verification_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    reset_password_token = Column(String(255), nullable=True, index=True)
    reset_password_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    department_record = relationship("Department", foreign_keys=[department_id])
    reporting_manager = relationship("User", remote_side=[id], foreign_keys=[reporting_manager_id])
    permission_grants = relationship(
        "UserPermission",
        foreign_keys="UserPermission.user_id",
        cascade="all, delete-orphan",
    )

    @property
    def department_name(self):
        return self.department_record.name if self.department_record else None


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(80), nullable=False)
    entity_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

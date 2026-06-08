from datetime import date

from sqlalchemy import String, Integer, ForeignKey, Table, Column, Date
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


article_tags = Table(
    "article_tags",
    Base.metadata,
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True, index=True),
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True, index=True),
)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)

    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        secondary="participations",
        back_populates="projects",
        viewonly=True
    )
    participations: Mapped[list["Participation"]] = relationship(
        back_populates="project",
        single_parent=True,
    )


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    projects = relationship(
        "Project",
        secondary="participations",
        back_populates="employees",
        viewonly=True
    )

    participations: Mapped[list["Participation"]] = relationship(
        back_populates="employee",
        single_parent=True,
    )


class Participation(Base):
    __tablename__ = "participations"

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), primary_key=True)

    role: Mapped[str] = mapped_column(String(50), nullable=False)

    project: Mapped["Project"] = relationship(back_populates="participations")
    employee: Mapped["Employee"] = relationship(back_populates="participations")






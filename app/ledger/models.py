from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.ledger.base import Base


class Bank(str, enum.Enum):
    SBI = "sbi"
    HDFC = "hdfc"


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    CLASSIFYING = "classifying"
    EXTRACTING = "extracting"
    RECONCILING = "reconciling"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    bank: Mapped[Bank] = mapped_column(SAEnum(Bank), nullable=False)
    account_number_masked: Mapped[str] = mapped_column(String(8), nullable=False)
    holder_name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    documents: Mapped[list["Document"]] = relationship(back_populates="account")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    file_sha256: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    bank: Mapped[Bank | None] = mapped_column(SAEnum(Bank), nullable=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False
    )
    status_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    txn_count_extracted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    txn_count_new: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    txn_count_duplicate: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    classified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    extracted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    account: Mapped[Account | None] = relationship(back_populates="documents")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="source_document")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("dedup_key", name="uq_transactions_dedup_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    description_raw: Mapped[str] = mapped_column(Text, nullable=False)
    description_normalized: Mapped[str] = mapped_column(Text, nullable=False)
    merchant_canonical: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    category_source: Mapped[str] = mapped_column(String(16), nullable=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_essential: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    balance_after_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dedup_key: Mapped[str] = mapped_column(String(64), nullable=False)
    within_day_counter: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    account: Mapped[Account] = relationship(back_populates="transactions")
    source_document: Mapped[Document] = relationship(back_populates="transactions")

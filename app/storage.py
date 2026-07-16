"""SQLAlchemy Core storage for TCGMARUHIT mutable state."""

from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Final

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.engine import Connection, Engine


SCHEMA_VERSION: Final[int] = 1
PREMIUM_DAYS: Final[int] = 30


class StorageProblem(RuntimeError):
    """An expected storage boundary failure with an HTTP-compatible status."""

    def __init__(self, code: str, status_code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class FreeLimitReached(StorageProblem):
    """The free collection limit was reached inside the write transaction."""

    def __init__(self, limit: int) -> None:
        super().__init__("free_limit", 403, f"무료 도감은 {limit}장까지 가능합니다.")
        self.limit = limit


class Storage:
    """Own the SQLAlchemy Core engine, schema, and short write transactions."""

    def __init__(self, database_url: str, *, clock: Callable[[], datetime] | None = None) -> None:
        self.database_url = database_url
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.metadata = MetaData()
        self.users = Table(
            "users",
            self.metadata,
            Column("device_id", String(255), primary_key=True),
            Column("premium", Boolean, nullable=False, default=False),
            Column("premium_until", DateTime(timezone=True), nullable=True),
            Column("joined_at", DateTime(timezone=True), nullable=False),
            Column("activated_at", DateTime(timezone=True), nullable=True),
            Column("updated_at", DateTime(timezone=True), nullable=False),
            Column("version", Integer, nullable=False, default=1),
        )
        self.payment_intents = Table(
            "payment_intents",
            self.metadata,
            Column("order_id", String(255), primary_key=True),
            Column("device_id", String(255), ForeignKey("users.device_id"), nullable=False),
            Column("amount", Integer, nullable=False),
            Column("status", String(32), nullable=False),
            Column("created_at", DateTime(timezone=True), nullable=False),
            Column("expires_at", DateTime(timezone=True), nullable=False),
        )
        self.payment_events = Table(
            "payment_events",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("payment_key", String(255), nullable=False, unique=True),
            Column("order_id", String(255), ForeignKey("payment_intents.order_id"), nullable=False, unique=True),
            Column("device_id", String(255), ForeignKey("users.device_id"), nullable=False),
            Column("amount", Integer, nullable=False),
            Column("status", String(32), nullable=False),
            Column("verified_at", DateTime(timezone=True), nullable=False),
        )
        self.collection_entries = Table(
            "collection_entries",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("device_id", String(255), ForeignKey("users.device_id"), nullable=False),
            Column("card_name", String(255), nullable=False),
            Column("cost", Integer, nullable=False),
            Column("current_price", Integer, nullable=False),
            Column("last_price", Integer, nullable=True),
            Column("added_at", DateTime(timezone=True), nullable=False),
            Column("price_updated_at", DateTime(timezone=True), nullable=True),
        )
        self.engine = self._make_engine(database_url)
        self.metadata.create_all(self.engine)

    @staticmethod
    def _make_engine(database_url: str) -> Engine:
        if database_url.startswith("sqlite"):
            return create_engine(
                database_url,
                connect_args={"check_same_thread": False, "timeout": 30},
            )
        return create_engine(
            database_url,
            pool_size=1,
            max_overflow=1,
            pool_timeout=5,
            pool_pre_ping=True,
        )

    @property
    def is_sqlite(self) -> bool:
        """Return whether the configured engine uses SQLite."""
        return self.engine.dialect.name == "sqlite"

    @contextmanager
    def transaction(self) -> Iterator[Connection]:
        """Run one short transaction, serializing SQLite writers."""
        connection = self.engine.connect()
        try:
            if self.is_sqlite:
                connection.exec_driver_sql("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:  # noqa: BROAD_EXCEPT_OK
            connection.rollback()
            raise
        finally:
            connection.close()

    def ensure_user(
        self,
        connection: Connection,
        device_id: str,
        now: datetime | None = None,
    ) -> Mapping[str, str | int | bool | datetime | None]:
        """Create and return a user row without touching legacy JSON files."""
        row = connection.execute(select(self.users).where(self.users.c.device_id == device_id)).mappings().first()
        if row is not None:
            return row
        current = now or self.clock()
        connection.execute(
            insert(self.users).values(
                device_id=device_id,
                premium=False,
                premium_until=None,
                joined_at=current,
                activated_at=None,
                updated_at=current,
                version=1,
            )
        )
        return connection.execute(select(self.users).where(self.users.c.device_id == device_id)).mappings().one()

    def get_user(self, device_id: str) -> Mapping[str, str | int | bool | datetime | None] | None:
        """Return a user row, or None when it has never been seen."""
        with self.engine.connect() as connection:
            return connection.execute(select(self.users).where(self.users.c.device_id == device_id)).mappings().first()

    def list_collection(self, device_id: str) -> list[dict[str, int | float | str | None]]:
        """Return collection entries owned by one device."""
        with self.engine.connect() as connection:
            rows = connection.execute(
                select(self.collection_entries).where(self.collection_entries.c.device_id == device_id).order_by(self.collection_entries.c.id)
            ).mappings().all()
        return [self._entry_json(row) for row in rows]

    def add_collection(self, device_id: str, card: Mapping[str, str | int | float | None], free_limit: int) -> dict[str, int | float | str | None]:
        """Check the free limit and insert one collection entry atomically."""
        now = self.clock()
        with self.transaction() as connection:
            user = self.ensure_user(connection, device_id, now)
            count = connection.execute(
                select(func.count()).select_from(self.collection_entries).where(self.collection_entries.c.device_id == device_id)
            ).scalar_one()
            if not self._is_premium(user, now) and count >= free_limit:
                raise FreeLimitReached(free_limit)
            result = connection.execute(
                insert(self.collection_entries).values(
                    device_id=device_id,
                    card_name=str(card.get("card_name") or card.get("name") or ""),
                    cost=int(card.get("cost") or 0),
                    current_price=int(card.get("current_price") or 0),
                    last_price=int(card["last_price"]) if card.get("last_price") is not None else None,
                    added_at=now,
                    price_updated_at=None,
                )
            )
            entry_id = int(result.inserted_primary_key[0])
            row = connection.execute(select(self.collection_entries).where(self.collection_entries.c.id == entry_id)).mappings().one()
        return self._entry_json(row)

    def delete_collection(self, device_id: str, entry_id: int) -> bool:
        """Delete only an entry matching both its id and owner."""
        with self.transaction() as connection:
            result = connection.execute(
                self.collection_entries.delete().where(
                    (self.collection_entries.c.id == entry_id) & (self.collection_entries.c.device_id == device_id)
                )
            )
        return result.rowcount == 1

    def refresh_collection(self, device_id: str, updates: Sequence[Mapping[str, int | float | None]]) -> int:
        """Update prices only for entries owned by the supplied device."""
        now = self.clock()
        updated = 0
        with self.transaction() as connection:
            for item in updates:
                entry_id = int(item.get("id") or 0)
                if entry_id <= 0:
                    continue
                result = connection.execute(
                    update(self.collection_entries)
                    .where((self.collection_entries.c.id == entry_id) & (self.collection_entries.c.device_id == device_id))
                    .values(
                        last_price=self.collection_entries.c.current_price,
                        current_price=int(item.get("current_price") or 0),
                        price_updated_at=now,
                    )
                )
                updated += result.rowcount
        return updated

    def create_payment_intent(self, order_id: str, device_id: str, amount: int, expires_at: datetime) -> dict[str, str | int]:
        """Persist a server-generated payment intent."""
        now = self.clock()
        with self.transaction() as connection:
            self.ensure_user(connection, device_id, now)
            connection.execute(
                insert(self.payment_intents).values(
                    order_id=order_id,
                    device_id=device_id,
                    amount=amount,
                    status="PENDING",
                    created_at=now,
                    expires_at=expires_at,
                )
            )
        return {"orderId": order_id, "device_id": device_id, "amount": amount, "expires_at": expires_at.isoformat()}

    def get_payment_intent(self, order_id: str) -> Mapping[str, str | int | datetime] | None:
        """Return a payment intent for pre-network ownership checks."""
        with self.engine.connect() as connection:
            return connection.execute(
                select(self.payment_intents).where(self.payment_intents.c.order_id == order_id)
            ).mappings().first()

    def apply_payment(
        self,
        order_id: str,
        payment_key: str,
        amount: int,
        *,
        requested_device_id: str | None = None,
    ) -> dict[str, str | bool | None]:
        """Consume an intent and activate its owner, idempotently."""
        now = self.clock()
        with self.transaction() as connection:
            by_key = connection.execute(
                select(self.payment_events).where(self.payment_events.c.payment_key == payment_key)
            ).mappings().first()
            by_order = connection.execute(
                select(self.payment_events).where(self.payment_events.c.order_id == order_id)
            ).mappings().first()
            existing = by_key or by_order
            if existing is not None:
                if requested_device_id is not None and existing["device_id"] != requested_device_id:
                    raise StorageProblem("payment_owner_mismatch", 403, "결제 소유자가 일치하지 않습니다.")
                if existing["payment_key"] != payment_key or existing["order_id"] != order_id or existing["amount"] != amount:
                    raise StorageProblem("payment_replay_conflict", 409, "이미 다른 결제 정보로 처리된 주문입니다.")
                user = connection.execute(select(self.users).where(self.users.c.device_id == existing["device_id"])).mappings().one()
                return self._subscription_json(user)

            intent = connection.execute(
                select(self.payment_intents).where(self.payment_intents.c.order_id == order_id)
            ).mappings().first()
            if intent is None:
                raise StorageProblem("payment_intent_not_found", 403, "유효한 결제 주문이 아닙니다.")
            if requested_device_id is not None and intent["device_id"] != requested_device_id:
                raise StorageProblem("payment_owner_mismatch", 403, "결제 소유자가 일치하지 않습니다.")
            if intent["amount"] != amount:
                raise StorageProblem("payment_amount_mismatch", 403, "결제 금액이 주문 금액과 다릅니다.")
            if intent["status"] != "PENDING":
                raise StorageProblem("payment_intent_used", 409, "이미 사용된 결제 주문입니다.")
            if _as_utc(intent["expires_at"]) <= now:
                raise StorageProblem("payment_intent_expired", 403, "만료된 결제 주문입니다.")

            user = self.ensure_user(connection, str(intent["device_id"]), now)
            previous_until = _as_utc(user["premium_until"]) if user["premium_until"] is not None else now
            premium_until = max(previous_until, now) + timedelta(days=PREMIUM_DAYS)
            connection.execute(
                insert(self.payment_events).values(
                    payment_key=payment_key,
                    order_id=order_id,
                    device_id=intent["device_id"],
                    amount=amount,
                    status="DONE",
                    verified_at=now,
                )
            )
            connection.execute(
                update(self.payment_intents).where(self.payment_intents.c.order_id == order_id).values(status="USED")
            )
            connection.execute(
                update(self.users)
                .where(self.users.c.device_id == intent["device_id"])
                .values(premium=True, premium_until=premium_until, activated_at=now, updated_at=now, version=self.users.c.version + 1)
            )
            return {"device_id": intent["device_id"], "premium": True, "premium_until": premium_until.isoformat()}

    def export_users(self) -> dict[str, dict[str, str | bool | int | None]]:
        """Export users in the legacy JSON-compatible shape."""
        with self.engine.connect() as connection:
            rows = connection.execute(select(self.users).order_by(self.users.c.device_id)).mappings().all()
        return {
            str(row["device_id"]): {
                "device_id": row["device_id"],
                "premium": bool(row["premium"]),
                "premium_until": _iso(row["premium_until"]),
                "joined": _iso(row["joined_at"]),
                "activated_at": _iso(row["activated_at"]),
                "updated_at": _iso(row["updated_at"]),
                "version": row["version"],
            }
            for row in rows
        }

    def export_collection(self) -> list[dict[str, int | float | str | None]]:
        """Export collection entries in the legacy JSON-compatible shape."""
        with self.engine.connect() as connection:
            rows = connection.execute(select(self.collection_entries).order_by(self.collection_entries.c.id)).mappings().all()
        return [self._entry_json(row) for row in rows]

    @staticmethod
    def _is_premium(user: Mapping[str, str | int | bool | datetime | None], now: datetime) -> bool:
        return bool(user["premium"]) and user["premium_until"] is not None and _as_utc(user["premium_until"]) > now

    @staticmethod
    def _entry_json(row: Mapping[str, str | int | bool | datetime | None]) -> dict[str, int | float | str | None]:
        cost = int(row["cost"])
        current = int(row["current_price"])
        profit = current - cost
        return {
            "id": int(row["id"]),
            "device_id": str(row["device_id"]),
            "name": str(row["card_name"]),
            "cost": cost,
            "current_price": current,
            "last_price": int(row["last_price"]) if row["last_price"] is not None else None,
            "added_at": _iso(row["added_at"]),
            "price_updated_at": _iso(row["price_updated_at"]),
            "profit": profit,
            "roi": round(profit / cost * 100, 1) if cost else 0,
        }

    @staticmethod
    def _subscription_json(user: Mapping[str, str | int | bool | datetime | None]) -> dict[str, str | bool | None]:
        return {"device_id": str(user["device_id"]), "premium": bool(user["premium"]), "premium_until": _iso(user["premium_until"])}


def _as_utc(value: str | int | bool | datetime | None) -> datetime:
    if not isinstance(value, datetime):
        return datetime.min.replace(tzinfo=timezone.utc)
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _iso(value: str | int | bool | datetime | None) -> str | None:
    return _as_utc(value).isoformat() if isinstance(value, datetime) else None

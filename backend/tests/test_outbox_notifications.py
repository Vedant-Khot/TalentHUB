import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event, select

from app.db.base import Base
from app.models.entities import User, NotificationLog
from app.models.enums import UserRole, NotificationChannel, NotificationStatus
from app.services.outbox_service import OutboxService

@pytest_asyncio.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.mark.asyncio
async def test_notification_outbox_and_retries(async_db: AsyncSession):
    user = User(email="notify@college.edu", password_hash="hash", role=UserRole.STUDENT)
    async_db.add(user)
    await async_db.commit()

    # 1. Queue a notification
    notif = await OutboxService.queue_notification(
        db=async_db,
        user_id=user.id,
        template_name="TEST_EVENT",
        payload={"message": "You are shortlisted"}
    )
    await async_db.commit()
    assert notif.id is not None
    assert notif.status == NotificationStatus.PENDING
    assert notif.retry_count == 0

    # 2. Simulate worker failure
    failed_items = await OutboxService.process_pending_notifications(
        db=async_db,
        simulate_failure_for_test=True
    )
    assert len(failed_items) == 1
    assert failed_items[0].retry_count == 1
    assert failed_items[0].status == NotificationStatus.FAILED
    assert failed_items[0].error_message is not None

    # 3. Simulate retry 2 failure
    failed_items_2 = await OutboxService.process_pending_notifications(
        db=async_db,
        simulate_failure_for_test=True
    )
    assert failed_items_2[0].retry_count == 2
    assert failed_items_2[0].status == NotificationStatus.FAILED

    # 4. Now succeed on retry 3
    success_items = await OutboxService.process_pending_notifications(
        db=async_db,
        simulate_failure_for_test=False
    )
    assert len(success_items) == 1
    assert success_items[0].retry_count == 3
    assert success_items[0].status == NotificationStatus.SENT
    assert success_items[0].error_message is None

    # 5. Subsequent run has nothing pending
    remaining = await OutboxService.process_pending_notifications(db=async_db)
    assert len(remaining) == 0

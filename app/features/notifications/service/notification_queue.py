"""Notification queue with debouncing for push notifications"""
import asyncio
import logging
from asyncio import Queue, get_event_loop
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.features.notifications.service.notification_service import NotificationService

logger = logging.getLogger(__name__)

# Global queues for notification processing (initialized lazily)
_main_queue: Optional[Queue] = None
_filtered_queue: Optional[Queue] = None
_workers_started = False


def _get_main_queue() -> Queue:
    """Get or create the main queue"""
    global _main_queue
    if _main_queue is None:
        _main_queue = Queue()
    return _main_queue


def _get_filtered_queue() -> Queue:
    """Get or create the filtered queue"""
    global _filtered_queue
    if _filtered_queue is None:
        _filtered_queue = Queue()
    return _filtered_queue


async def main_queue_worker():
    """
    Debounce notifications - cancels duplicates within 1s window.

    When multiple notifications for the same user arrive rapidly,
    only the last one is actually sent after a 1-second delay.
    """
    main_queue = _get_main_queue()
    filtered_queue = _get_filtered_queue()
    delays_list = []

    logger.info("Main notification queue worker started")

    while True:
        notification_data = await main_queue.get()

        try:
            user_id = notification_data.get("user_id")

            # Cancel existing delayed notification for same user
            existing = [d for d in delays_list if d[0].get("user_id") == user_id]
            for delay_tuple in existing:
                delay_tuple[1].cancel()
                delays_list.remove(delay_tuple)

            # Schedule new notification with 1s delay
            loop = get_event_loop()
            callback = loop.call_later(
                1,  # 1 second debounce delay
                lambda data=notification_data: filtered_queue.put_nowait(data)
            )
            delays_list.append((notification_data, callback))

            logger.debug(f"Queued notification for user {user_id}, debounce pending")

        except Exception as e:
            logger.error(f"Error in main queue worker: {e}")
        finally:
            main_queue.task_done()


async def filtered_queue_worker(notification_service: "NotificationService"):
    """
    Process debounced notifications from the filtered queue.

    Notifications arriving here have passed the debounce filter and
    should be sent to all the user's registered devices.
    """
    filtered_queue = _get_filtered_queue()

    logger.info("Filtered notification queue worker started")

    while True:
        notification_data = await filtered_queue.get()

        try:
            user_id = notification_data.get("user_id")
            notification = notification_data.get("notification")

            logger.debug(f"Processing notification for user {user_id}")

            await notification_service.send_to_user(user_id, notification)

        except Exception as e:
            logger.error(f"Error in filtered queue worker: {e}")
        finally:
            filtered_queue.task_done()


async def queue_notification(user_id: int, notification: dict):
    """
    Add a notification to the debouncing queue (async).

    Args:
        user_id: Target user ID
        notification: Notification payload (with ios/android keys)
    """
    main_queue = _get_main_queue()
    await main_queue.put({
        "user_id": user_id,
        "notification": notification
    })


def queue_notification_sync(user_id: int, notification: dict):
    """
    Add a notification to the debouncing queue (sync - for use from scheduler).

    This can be called from sync code (like APScheduler jobs).

    Args:
        user_id: Target user ID
        notification: Notification payload (with ios/android keys)
    """
    main_queue = _get_main_queue()
    try:
        loop = get_event_loop()
        if loop.is_running():
            # If event loop is running, use call_soon_threadsafe
            loop.call_soon_threadsafe(
                main_queue.put_nowait,
                {"user_id": user_id, "notification": notification}
            )
        else:
            # If no running loop, just put directly
            main_queue.put_nowait({
                "user_id": user_id,
                "notification": notification
            })
    except RuntimeError:
        # No event loop - queue directly
        main_queue.put_nowait({
            "user_id": user_id,
            "notification": notification
        })


async def start_notification_workers(notification_service: "NotificationService"):
    """
    Start the notification queue worker tasks.

    Should be called during application startup in the lifespan context.

    Args:
        notification_service: NotificationService instance for sending notifications
    """
    global _workers_started

    if _workers_started:
        logger.warning("Notification workers already started")
        return

    _workers_started = True

    # Start both workers as background tasks
    asyncio.create_task(main_queue_worker())
    asyncio.create_task(filtered_queue_worker(notification_service))

    logger.info("Notification queue workers started")
    print("📲 Notification queue workers started")

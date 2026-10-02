import enum


class BookingStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    EXPIRED = "expired"

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"
    HOST = "host"

class NotificationType(enum.Enum):
    BOOKING_CREATED = "booking_created"
    BOOKING_CONFIRMED = "booking_confirmed"
    NEW_MESSAGE = "new_message"
    NEW_REVIEW = "new_review"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_EXPIRED = "booking_expired"
    BOOKING_COMPLETED = "booking_completed"
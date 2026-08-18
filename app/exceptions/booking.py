class BookingError(Exception):
    pass

class PropertyNotFoundException(BookingError):
    pass

class InvalidBookingDatesException(BookingError):
    pass

class BookingConflictException(BookingError):
    pass


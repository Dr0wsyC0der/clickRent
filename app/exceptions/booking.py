class BookingError(Exception):
    pass

class PropertyNotFoundException(BookingError):
    pass

class InvalidBookingDatesException(BookingError):
    pass

class BookingConflictException(BookingError):
    pass

class BookingNotFoundException(BookingError):
    pass

class BookingAccessDeniedException(BookingError):
    pass

class BookingStatusException(BookingError):
    pass
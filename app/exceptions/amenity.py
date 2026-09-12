class AmenityError(Exception):
    pass

class AmenityNotFoundException(AmenityError):
    pass

class AmenityAlreadyAddedException(AmenityError):
    pass

class AmenityNotAddedException(AmenityError):
    pass
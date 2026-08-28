class ReviewError(Exception):
    pass

class ReviewAlreadyExistsException(ReviewError):
    pass

class ReviewNotFoundException(ReviewError):
    pass

class ReviewAccessDeniedException(ReviewError):
    pass
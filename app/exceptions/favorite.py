class FavoriteError(Exception):
    pass

class AlreadyAddedToFavoritesException(FavoriteError):
    pass

class FavoriteNotFoundException(FavoriteError):
    pass
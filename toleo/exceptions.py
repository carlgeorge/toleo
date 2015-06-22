class ToleoError(Exception):
    pass


class NotFoundError(ToleoError):
    pass


class ApiError(ToleoError):
    pass

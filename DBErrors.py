class DatabaseException(Exception):
    pass

class UserExistError(DatabaseException):
    pass

class TableCreateError(DatabaseException):
    pass
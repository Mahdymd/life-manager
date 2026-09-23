"""core/domain/exceptions.py — سلسله‌مراتب exception های سفارشی."""


class AppError(Exception):
    def __init__(self, message: str, code: str = "UNKNOWN") -> None:
        super().__init__(message)
        self.message = message
        self.code = code

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class DatabaseError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "DB_ERROR")


class MigrationError(DatabaseError):
    def __init__(self, version: int, message: str) -> None:
        super().__init__(f"Migration v{version:03d} failed: {message}")
        self.version = version


class RecordNotFoundError(DatabaseError):
    def __init__(self, entity: str, id_: int) -> None:
        super().__init__(f"{entity} با شناسه {id_} پیدا نشد.")
        self.entity = entity
        self.id = id_


class ValidationError(AppError):
    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"{field}: {message}", "VALIDATION_ERROR")
        self.field = field


class RequiredFieldError(ValidationError):
    def __init__(self, field: str) -> None:
        super().__init__(field, "این فیلد الزامی است.")


class InvalidValueError(ValidationError):
    def __init__(self, field: str, value: object, expected: str = "") -> None:
        msg = f"مقدار '{value}' نامعتبر است."
        if expected:
            msg += f" مورد انتظار: {expected}"
        super().__init__(field, msg)


class BusinessRuleError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "BUSINESS_RULE")


class CircularDependencyError(BusinessRuleError):
    def __init__(self, entity: str) -> None:
        super().__init__(f"ارجاع دایره‌ای در {entity} شناسایی شد.")


class BackupError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "BACKUP_ERROR")


class RestoreError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "RESTORE_ERROR")

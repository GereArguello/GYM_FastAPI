from enum import Enum


class StatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class ProductType(str, Enum):
    MONEY = "money"
    POINTS = "points"

class RoleEnum(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"

class MembershipStatusEnum(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    INACTIVE = "inactive"

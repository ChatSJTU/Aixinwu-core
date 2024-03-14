from enum import Enum


class DonationErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    PERMISSION_DENIED = "permission_denied"
    REQUIRED = "required"
    CANNOT_ASSIGN_NODE = "cannot_assign_node"

from app.schemas.common import ResponseModel, PageParams, PageResult
from app.schemas.auth import LoginRequest, Token, TokenData, UserInfo
from app.schemas.user import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionCreate, PermissionUpdate, PermissionResponse,
    UserCreate, UserUpdate, UserPasswordUpdate, UserResponse,
)
from app.schemas.member import (
    MemberLevelCreate, MemberLevelUpdate, MemberLevelResponse,
    MemberTagCreate, MemberTagUpdate, MemberTagResponse,
    MemberCreate, MemberUpdate, MemberResponse,
    CoinRechargeRequest, PointRechargeRequest,
    CoinRecordResponse, PointRecordResponse,
)
from app.schemas.venue import (
    VenueTypeCreate, VenueTypeUpdate, VenueTypeResponse,
    VenueCreate, VenueUpdate, VenueResponse,
)
from app.schemas.reservation import (
    ReservationCreate, ReservationUpdate, ReservationResponse,
)
from app.schemas.coach import (
    CoachCreate, CoachUpdate, CoachResponse,
    CoachScheduleCreate, CoachScheduleUpdate, CoachScheduleResponse,
    CoachApplicationResponse, CoachApplicationAudit,
)

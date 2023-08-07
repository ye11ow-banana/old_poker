from auth.models import User
from repository import SQLAlchemyRepository


class UserRepository(SQLAlchemyRepository):
    model = User

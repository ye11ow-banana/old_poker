import pytest
from httpx import AsyncClient
from sqlalchemy import select

from auth.models import User
from database import async_session_maker

pytestmark = pytest.mark.asyncio


class TestLogin:
    _url = "/auth/login"
    _hashed_password = (
        "$2b$12$q.w27JQIcsvQFz75UFRKZ.K3P4qAxSb84JjcKgO/7rXcs0sLAxjEK"
    )

    async def test_success(self, ac: AsyncClient):
        async with async_session_maker() as session:
            user = User(
                username="login", hashed_password=self._hashed_password
            )
            session.add(user)
            await session.commit()
        response = await ac.post(
            self._url,
            json={
                "username": "login",
                "password": "string",
            },
        )
        access_token = response.json()["detail"]["token"]["access_token"]
        assert response.status_code == 200
        assert response.json() == {
            "detail": {
                "result": True,
                "token": {
                    "access_token": access_token,
                    "token_type": "bearer",
                },
            }
        }
        assert len(access_token) == 124
        assert len(access_token.split(".")) == 3
        assert (
            access_token.split(".")[0]
            == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        )

    async def test_no_data(self, ac: AsyncClient):
        response = await ac.post(self._url, json={})
        assert response.status_code == 401
        assert response.json() == {"detail": "Could not validate credentials"}

    async def test_empty_username(self, ac: AsyncClient):
        response = await ac.post(
            self._url,
            json={
                "username": "",
                "password": self._hashed_password,
            },
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Could not validate credentials"}

    async def test_empty_password(self, ac: AsyncClient):
        response = await ac.post(
            self._url,
            json={
                "username": "string",
                "password": "",
            },
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Could not validate credentials"}

    async def test_wrong_username(self, ac: AsyncClient):
        async with async_session_maker() as session:
            user = User(
                username="wrong_login", hashed_password=self._hashed_password
            )
            session.add(user)
            await session.commit()
        response = await ac.post(
            self._url,
            json={
                "username": "wrong",
                "password": self._hashed_password,
            },
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Could not validate credentials"}


class TestGetCurrentUser:
    _url = "/auth/users/me"
    _hashed_password = (
        "$2b$12$q.w27JQIcsvQFz75UFRKZ.K3P4qAxSb84JjcKgO/7rXcs0sLAxjEK"
    )
    _jwt_token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiJjdXJyZW50IiwiZXhwIjoxNzA2MTI2MTUyfQ."
        "GI1ZrYhtaWiBm5MQHezJTt9fYkIJV7X5L22xkL01z3s"
    )

    async def test_success(self, ac: AsyncClient):
        async with async_session_maker() as session:
            user = User(
                username="current", hashed_password=self._hashed_password
            )
            session.add(user)
            await session.commit()
        response = await ac.get(
            self._url,
            headers={"Authorization": f"Bearer {self._jwt_token}"},
        )
        assert response.status_code == 200
        assert response.json() == {
            "detail": {
                "result": True,
                "user": {
                    "id": str(user.id),
                    "username": "current",
                },
            }
        }

    async def test_no_token(self, ac: AsyncClient):
        response = await ac.get(self._url)
        assert response.status_code == 401
        assert response.json() == {"detail": "Could not validate credentials"}


class TestRegistration:
    _url = "/auth/registration"

    async def test_success(self, ac: AsyncClient):
        response = await ac.post(
            self._url,
            json={
                "username": "string",
                "password": "string",
                "repeat_password": "string",
            },
        )
        new_id = response.json()["detail"]["user"]["id"]
        assert response.status_code == 201
        assert response.json() == {
            "detail": {
                "result": True,
                "user": {
                    "id": new_id,
                    "username": "string",
                },
            }
        }
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).filter_by(username="string")
            )
            result = result.scalars().first()
            assert str(result.id) == new_id
            assert result.username == "string"

    async def test_no_data(self, ac: AsyncClient):
        async with async_session_maker() as session:
            old_results = (await session.execute(select(User))).scalars().all()
        response = await ac.post("/auth/registration", json={})
        assert response.status_code == 400
        assert response.json() == {
            "detail": {
                "errors": [
                    {"field": "username", "message": "Field required"},
                    {"field": "password", "message": "Field required"},
                    {"field": "repeat_password", "message": "Field required"},
                ],
                "result": False,
            }
        }
        async with async_session_maker() as session:
            result = await session.execute(select(User))
            assert len(result.scalars().all()) == len(old_results)

    async def test_empty_username(self, ac: AsyncClient):
        async with async_session_maker() as session:
            old_results = (await session.execute(select(User))).scalars().all()
        response = await ac.post(
            self._url,
            json={
                "username": "",
                "password": "string",
                "repeat_password": "string",
            },
        )
        assert response.status_code == 400
        assert response.json() == {
            "detail": {
                "errors": [
                    {
                        "field": "username",
                        "message": "String should have at least 3 characters",
                    }
                ],
                "result": False,
            }
        }
        async with async_session_maker() as session:
            result = await session.execute(select(User))
            assert len(result.scalars().all()) == len(old_results)

    async def test_empty_password(self, ac: AsyncClient):
        async with async_session_maker() as session:
            old_results = (await session.execute(select(User))).scalars().all()
        response = await ac.post(
            self._url,
            json={
                "username": "string",
                "password": "",
                "repeat_password": "string",
            },
        )
        assert response.status_code == 400
        assert response.json() == {
            "detail": {
                "errors": [
                    {
                        "field": "password",
                        "message": "String should have at least 6 characters",
                    },
                    {
                        "field": "repeat_password",
                        "message": "Passwords do not match",
                    },
                ],
                "result": False,
            }
        }
        async with async_session_maker() as session:
            result = await session.execute(select(User))
            assert len(result.scalars().all()) == len(old_results)

    async def test_empty_repeat_password(self, ac: AsyncClient):
        async with async_session_maker() as session:
            old_results = (await session.execute(select(User))).scalars().all()
        response = await ac.post(
            self._url,
            json={
                "username": "string",
                "password": "string",
                "repeat_password": "",
            },
        )
        assert response.status_code == 400
        assert response.json() == {
            "detail": {
                "errors": [
                    {
                        "field": "repeat_password",
                        "message": "Passwords do not match",
                    }
                ],
                "result": False,
            }
        }
        async with async_session_maker() as session:
            result = await session.execute(select(User))
            assert len(result.scalars().all()) == len(old_results)

    async def test_username_already_exists(self, ac: AsyncClient):
        async with async_session_maker() as session:
            user = User(username="existing_username", hashed_password="string")
            session.add(user)
            await session.commit()
            old_results = (await session.execute(select(User))).scalars().all()
        response = await ac.post(
            self._url,
            json={
                "username": "existing_username",
                "password": "string",
                "repeat_password": "string",
            },
        )
        assert response.status_code == 400
        assert response.json() == {
            "detail": {
                "errors": [
                    {
                        "field": "all",
                        "message": "User with this username already exists",
                    }
                ],
                "result": False,
            }
        }
        async with async_session_maker() as session:
            result = await session.execute(select(User))
            assert len(result.scalars().all()) == len(old_results)

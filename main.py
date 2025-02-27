import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sqlalchemy
from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import jwt

app = FastAPI()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

handler = logging.FileHandler('app.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.info("Logging is configured, the application is starting...")

# Загрузка переменных окружения
load_dotenv('load_dotenv.env')

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

DATABASE_URL = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
if None in [DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]:
    logger.error("One or more database configuration variables are not set.")
    raise ValueError("One or more database configuration variables are not set.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = sqlalchemy.orm.declarative_base()

security = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Конфигурация JWT
SECRET_KEY = os.getenv("SECRET_KEY", "mysecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

fake_users_db = {
    "dockerr": {
        "hashed_password": pwd_context.hash("secret"),
        "role": "admin"
    },
    "user0": {
        "hashed_password": pwd_context.hash("userpass"),
        "role": "user"
    }
}

class User(BaseModel):
    username: str
    role: str

class UserInDB(User):
    hashed_password: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str):
    user = fake_users_db.get(username)
    if user:
        return UserInDB(**user)
    return None

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(security)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = User(username=username, role=payload.get("role"))
    except jwt.PyJWTError:
        raise credentials_exception
    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception
    return user

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Определяем модели
class FootballClubCreate(BaseModel):
    name: str

# Определяем модели
class Player(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    surname = Column(String, nullable=True)
    lastname = Column(String, nullable=False)
    id_clubss = Column(Integer, nullable=True)


class Statistic(Base):
    __tablename__ = 'statistics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_players = Column(Integer, ForeignKey('players.id', ondelete='CASCADE'), nullable=False)
    date_of_goal = Column(String, nullable=False)


class FootballClub(Base):
    __tablename__ = 'football_clubss'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)


Base.metadata.create_all(engine)

# Пример использования логирования:
@app.post("/football_clubss")
async def create_football_club(
        club: FootballClubCreate,
        current_user: str = Depends(lambda: get_current_active_user(required_roles=['admin']))
):
    session: SQLAlchemySession = SessionLocal()
    try:
        new_club = FootballClub(name=club.name)
        session.add(new_club)
        session.commit()
        logger.info("Football club created successfully.")
        return {"detail": "Football club created successfully", "club": new_club}
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to create football club: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.post("/statistics")
async def create_statistic(
        id_players: int = Body(...),
        date_of_goal: str = Body(...),
        current_user: str = Depends(lambda: get_current_active_user(required_roles=['admin']))
):
    session: SQLAlchemySession = SessionLocal()
    try:
        new_statistic = Statistic(id_players=id_players, date_of_goal=date_of_goal)
        session.add(new_statistic)
        session.commit()
        return {"detail": "Statistic created successfully", "statistic": new_statistic}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.put("/statistics/{statistic_id}")
async def update_statistic(
        statistic_id: int,
        id_players: int = Body(...),
        date_of_goal: str = Body(...),
        current_user: str = Depends(lambda: get_current_active_user(required_roles=['admin']))
):
    session: SQLAlchemySession = SessionLocal()
    try:
        statistic = session.query(Statistic).filter(Statistic.id == statistic_id).first()
        if statistic is None:
            raise HTTPException(status_code=404, detail="Statistic not found")

        # Обновляем поля статистики
        statistic.id_players = id_players
        statistic.date_of_goal = date_of_goal

        session.commit()
        return {"detail": "Statistic updated successfully", "statistic": statistic}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.get("/")
async def read_players():
    session: SQLAlchemySession = SessionLocal()
    try:
        players = session.query(Player).all()
        return players
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.get("/my_stats")
async def get_my_stats(current_user: str = Depends(lambda: get_current_active_user(required_roles=['user']))):
    @app.get("/my_stats")
    async def get_my_stats(current_user: str = Depends(lambda: get_current_active_user(required_roles=['user']))):
        session: SQLAlchemySession = SessionLocal()

        try:
            # Получаем ID игрока на основе user_id (который совпадает с username текущего пользователя)
            player = session.query(Player).filter(Player.user_id == current_user).first()

            if player is None:
                raise HTTPException(status_code=404, detail="Player not found")

            # Получаем статистику для этого игрока
            statistics = session.query(Statistic).filter(Statistic.id_players == player.id).all()

            return statistics
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            session.close()


@app.delete("/players/{player_id}")
async def delete_player(
        player_id: int,
        current_user: str = Depends(lambda: get_current_active_user(required_roles=['admin']))
):
    session: SQLAlchemySession = SessionLocal()
    try:
        # Сначала удаляем все статистики, связанные с игроком
        session.query(Statistic).filter(Statistic.id_players == player_id).delete()

        # Теперь удаляем игрока
        player = session.query(Player).filter(Player.id == player_id).first()
        if player is None:
            raise HTTPException(status_code=404, detail="Player not found")

        session.delete(player)
        session.commit()
        return {"detail": "Player deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

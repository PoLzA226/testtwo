import os
from dotenv import load_dotenv
import sqlalchemy
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body

# Укажите путь к вашему файлу .env
load_dotenv('load_dotenv.env')  # Загружаем переменные окружения из указанного файла

app = FastAPI()

#app.add_middleware(
 #  allow_origins=["*"],  # Замените на ваш сайт, если необходимо
  #  allow_credentials=True,
   # allow_methods=["*"],
    #allow_headers=["*"],
#)

# Конфигурация базы данных
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

# Создаем строку подключения
DATABASE_URL = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
if None in [DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]:
    raise ValueError("One or more database configuration variables are not set.")

# Создаем движок базы данных
engine = create_engine(DATABASE_URL)
# Создаем сессию
SessionLocal = sessionmaker(bind=engine)

# Определяем базовый класс
Base = sqlalchemy.orm.declarative_base()

# Определяем модели
class Player(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    surname = Column(String, nullable=True)
    lastname = Column(String, nullable=False)
    id_clubss = Column(Integer, nullable=True)

# Создаем все таблицы
Base.metadata.create_all(engine)

@app.post("/players/")
async def create_player(
    name: str = Body(...),
    surname: str = Body(...),
    lastname: str = Body(...),
    id_clubss: int = Body(None)
):
    session: SQLAlchemySession = SessionLocal()
    try:
        new_player = Player(name=name, surname=surname, lastname=lastname, id_clubss=id_clubss)
        session.add(new_player)  # Добавляем нового игрока
        session.commit()  # Подтверждаем изменения
        return {"detail": "Player created successfully", "player": new_player}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@app.get("/")
async def read_players():
    session: SQLAlchemySession = SessionLocal()
    try:
        # Извлекаем всех игроков
        players = session.query(Player).all()
        return players  # Возвращаем список игроков
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@app.delete("/players/{player_id}")
async def delete_player(player_id: int):
    session: SQLAlchemySession = SessionLocal()
    try:
        # Ищем игрока по ID
        player = session.query(Player).filter(Player.id == player_id).first()
        if player is None:
            raise HTTPException(status_code=404, detail="Player not found")

        session.delete(player)  # Удаляем игрока
        session.commit()  # Подтверждаем изменения
        return {"detail": "Player deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
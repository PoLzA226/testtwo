import os
from dotenv import load_dotenv
import sqlalchemy
from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession


# Укажите путь к вашему файлу .env
load_dotenv('load_dotenv.env')  # Загружаем переменные окружения из указанного файла
app = FastAPI()

# Конфигурация базы данных
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

print("Текущие переменные окружения:")
print(f"DB_USER:", DB_USER)
print(f"DB_PASSWORD: {os.environ.get('DB_PASSWORD')}")
print(f"DB_HOST: {os.environ.get('DB_HOST')}")
print(f"DB_PORT: {os.environ.get('DB_PORT')}")
print(f"DB_NAME: {os.environ.get('DB_NAME')}")

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


@app.get("/")
async def read_players():
    session: SQLAlchemySession = SessionLocal()
    try:
        # Извлекаем всех игроков
        players = session.query(Player).all()
        return players  # Возвращаем список игроков
    except Exception as e:
        return {"error": str(e)}
    finally:
        session.close()


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
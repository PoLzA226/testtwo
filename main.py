import os
from dotenv import load_dotenv
import sqlalchemy
from fastapi import FastAPI, HTTPException, Body
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession

load_dotenv('load_dotenv.env')

app = FastAPI()

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

DATABASE_URL = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
if None in [DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]:
    raise ValueError("One or more database configuration variables are not set.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = sqlalchemy.orm.declarative_base()


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


Base.metadata.create_all(engine)


@app.post("/statistics")
async def create_statistic(
        id: int = Body(...),
        id_players: int = Body(...),
        date_of_goal: str = Body(...)
):
    session: SQLAlchemySession = SessionLocal()
    try:
        new_statistic = Statistic(id=id, id_players=id_players, date_of_goal=date_of_goal)
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
        date_of_goal: str = Body(...)
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


@app.delete("/players/{player_id}")
async def delete_player(player_id: int):
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

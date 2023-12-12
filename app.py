# endpoints:
# GET /leaderboard?page=x (x es el número de pagina). devuelve la lista de 10 jugadores con sus datos.
# POST /newEntry. dados pname, floors, kills, bossKills y time. devuelve el ranking del jugador.

from flask import Flask, request
import pickle
import os.path

class LeaderboardEntry:
    def __init__(self, pname: str, floors: int, kills: int, bossKills: int, time: int):
        self.pname = pname
        self.floors = floors
        self.kills = kills
        self.bossKills = bossKills
        self.time = time

    def serialize(self):
        return {
            "pname": self.pname,
            "floors": self.floors,
            "kills": self.kills,
            "bossKills": self.bossKills,
            "time": self.time
        }

    def __str__(self):
        return self.pname


app = Flask(__name__)
leaderboard_db: list[LeaderboardEntry]

PAGE_SIZE = 8


# region Métodos GET
@app.route('/', methods=['GET'])
def hello_world() -> str:
    return f"""Hola! rest api roguelike. uso:
        - GET /leadeboard (solo los {PAGE_SIZE} primeros)
        - GET /leaderboard?page=x (paginado {PAGE_SIZE} jugadores a la vez, empezando por 0)
        - POST /newEntry (dados pname, floors, kills, bossKills y time)
    """


@app.route('/leaderboard', methods=['GET'])
def get_leaderboard() -> dict:
    page = request.args.get("page", 0, type=int)
    print(f"splicing at page {page}!!")

    if page > (len(leaderboard_db) // PAGE_SIZE):
        return {"leaderboard": []}
    return {"leaderboard": [entry.serialize() for entry in leaderboard_db[page * PAGE_SIZE: (page + 1) * PAGE_SIZE]]}

# endregion


# region Métodos POST
@app.route('/newEntry', methods=['POST'])
def new_entry():
    entry = LeaderboardEntry(pname=request.json['pname'],
                             floors=request.json['floors'],
                             kills=request.json['kills'],
                             bossKills=request.json['bossKills'],
                             time=request.json['time'])
    add_entry_and_save(entry)
    return {'pname':request.json['pname']}
# endregion


def add_entry_and_save(entry: LeaderboardEntry) -> None:
    leaderboard_db.append(entry)
    with open("leaderboard.pkl", "wb") as f:
        pickle.dump(leaderboard_db, f)
    print(f"saved {entry}!!")


# TODO: cargar datos de archivo a variable de db
def _load_db() -> list[LeaderboardEntry]:
    loaded_leaderboard: list[LeaderboardEntry] = []
    if(not os.path.isfile("leaderboard.pkl")):
        return loaded_leaderboard
    
    with open("leaderboard.pkl", "rb") as f:
        for entry in pickle.load(f):
            if type(entry) is LeaderboardEntry:
                loaded_leaderboard.append(entry)
            else:
                print(f"entry {entry} of type {type(entry)} is invalid!!")

    return loaded_leaderboard


def _populate_test_db() -> None:
    j = LeaderboardEntry("vic", 1, 2, 3, 4)
    add_entry_and_save(j)


with app.app_context():
    leaderboard_db = _load_db()
    if(not os.path.isfile("leaderboard.pkl")):
       _populate_test_db()
    print(leaderboard_db)


if __name__ == '__main__':
    app.run()

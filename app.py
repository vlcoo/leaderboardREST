# endpoints:
# GET /leaderboard?page=x (x es el número de pagina). devuelve la lista de 10 jugadores con sus datos.
# POST /newEntry. dados pname, floors, kills, bossKills y time. devuelve el ranking del jugador.

from flask import Flask, request
from jsonschema import validate
import pickle
import os.path
import enum


class SortType(enum.Enum):
    SCORE = "score"
    FLOORS = "floors"
    KILLS = "kills"
    BOSS_KILLS = "boss_kills"
    TIME = "time"


class LeaderboardEntry:
    def __init__(self, pname: str, floors: int, kills: int, boss_kills: int, time: int):
        self.pname = pname
        self.floors = floors
        self.kills = kills
        self.boss_kills = boss_kills
        self.time = time
        self.score = self.get_score()

    def __lt__(self, other):
        return self.get_score() < other.get_score()

    def serialize(self) -> dict:
        return {
            "pname": self.pname,
            "floors": self.floors,
            "kills": self.kills,
            "boss_kills": self.boss_kills,
            "time": self.time,
            "score": self.get_score(),
        }

    def get_score(self) -> int:
        return self.kills * 200 + self.boss_kills * 2000 + self.floors * 750 + self.time * -1

    def __str__(self):
        return f"{self.pname} ({self.score} pts.)"


app = Flask(__name__)
leaderboard_db: list[LeaderboardEntry]

PAGE_SIZE = 8
SCHEMA = {
    "type": "object",
    "properties": {
        "pname": {"type": "string", "minLength": 1, "maxLength": 12},
        "floors": {"type": "integer", "minimum": 0},
        "kills": {"type": "integer", "minimum": 0},
        "boss_kills": {"type": "integer", "minimum": 0},
        "time": {"type": "integer", "minimum": 0},
    },
    "required": ["pname", "floors", "kills", "boss_kills", "time"],
}


# region Métodos GET
@app.route('/', methods=['GET'])
def hello_world() -> str:
    return f"""Hola! rest api roguelike. uso:
        - GET /leaderboard (metadatos sobre la paginacion.)
        - GET /leaderboard?page=x (paginado {PAGE_SIZE} jugadores a la vez, empezando por 0.)
        - GET /leaderboard?sort=x (ordenar la lista de scores. metodos disponibles: {', '.join([sort_type.value for sort_type in SortType])}.)
        - GET /leaderboard/x (filtrar base de datos por nombre de jugador, soporta page y sort.)
        - POST /newEntry (dados pname, floors, kills, bossKills y time.)
    """


@app.route('/leaderboard', methods=['GET'])
def get_leaderboard() -> dict:
    if "page" not in request.args:
        return {
            "player_count": len(leaderboard_db),
            "players_per_page": PAGE_SIZE,
        }

    page = request.args.get("page", 0, type=int)
    sort_type = request.args.get("sort", SortType.SCORE.value, type=str)

    return {"leaderboard": [entry.serialize() for entry in get_sorted_filtered_paginated_leaderboard(sort_type, page=page)]}


@app.route('/leaderboard/<string:pname>', methods=['GET'])
def get_leaderboard_by_name(pname: str) -> dict:
    page = request.args.get("page", 0, type=int)
    sort_type = request.args.get("sort", SortType.SCORE.value, type=str)

    return {"leaderboard": [entry.serialize() for entry in get_sorted_filtered_paginated_leaderboard(sort_type, pname, page)]}


@app.route('/leaderboard/clear', methods=['GET'])
def clear_db() -> str:
    global leaderboard_db
    entries = len(leaderboard_db)

    with open("leaderboard.pkl", "wb") as f:
        pickle.dump([], f)
    leaderboard_db = _load_db()

    return f"cleared {entries} entries..."


# endregion


# region Métodos POST
@app.route('/newEntry', methods=['POST'])
def new_entry() -> str:
    try:
        validate(request.json, SCHEMA)
    except Exception as e:
        return f"invalid json: {str(e).splitlines()[0]}"

    entry = LeaderboardEntry(pname=request.json['pname'],
                             floors=request.json['floors'],
                             kills=request.json['kills'],
                             boss_kills=request.json['boss_kills'],
                             time=request.json['time'])
    add_entry_and_save(entry)
    return entry.pname


# endregion


# returns the sliced leaderboard, sorted by the given method and optionally filtered by a player name.
def get_sorted_filtered_paginated_leaderboard(sort_type: str, player_name: str = "", page: int = 0) -> list[LeaderboardEntry]:
    print(f"splicing at page {page}...")
    if page > (len(leaderboard_db) // PAGE_SIZE) or not leaderboard_db:
        print("...but page is off-limits.")
        return []

    trimmed_leaderboard = [entry for entry in leaderboard_db if (player_name.lower() in entry.pname.lower() or player_name == "")]

    if sort_type not in [sort_type.value for sort_type in SortType]:
        sort_type = SortType.SCORE.value
    return sorted(trimmed_leaderboard, key=lambda entry: getattr(entry, sort_type), reverse=True)[page * PAGE_SIZE: (page + 1) * PAGE_SIZE]


# adds an entry to the leaderboard list and saves it to file
def add_entry_and_save(entry: LeaderboardEntry) -> None:
    leaderboard_db.append(entry)
    with open("leaderboard.pkl", "wb") as f:
        pickle.dump(leaderboard_db, f)
    print(f"saved {entry}!!")


# loads the leaderboard list from file. if file doesn't exist, creates it. returns the loaded list
def _load_db() -> list[LeaderboardEntry]:
    loaded_leaderboard: list[LeaderboardEntry] = []

    # only load from file if it contains stuff. if not we can just use the empty list
    if not _create_db():
        with open("leaderboard.pkl", "rb") as f:
            for entry in pickle.load(f):
                if type(entry) is LeaderboardEntry:
                    loaded_leaderboard.append(entry)
                else:
                    print(f"entry {entry} of type {type(entry)} is invalid!!")

    return loaded_leaderboard


# returns true if database file didn't exist and was created
def _create_db() -> bool:
    if not os.path.isfile("leaderboard.pkl"):
        print("leaderboard file not found, creating new one!!")

        with open("leaderboard.pkl", "wb") as f:
            pickle.dump([], f)
        return True

    return False


with app.app_context():
    leaderboard_db = _load_db()

if __name__ == '__main__':
    app.run()

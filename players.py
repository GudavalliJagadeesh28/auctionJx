from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class Player:
    id: int
    name: str
    country: str
    role: str
    style: str
    base_price_lakh: int


_ROSTERS = {
    "Batter": [
        ("Virat Kohli", "India", "Right-hand top order"), ("Rohit Sharma", "India", "Right-hand opener"),
        ("Shubman Gill", "India", "Right-hand top order"), ("Yashasvi Jaiswal", "India", "Left-hand opener"),
        ("Suryakumar Yadav", "India", "Right-hand middle order"), ("Ruturaj Gaikwad", "India", "Right-hand opener"),
        ("KL Rahul", "India", "Right-hand batter and wicketkeeper"), ("Shreyas Iyer", "India", "Right-hand middle order"),
        ("Rishabh Pant", "India", "Left-hand batter and wicketkeeper"), ("Sanju Samson", "India", "Right-hand batter and wicketkeeper"),
        ("Tilak Varma", "India", "Left-hand middle order"), ("Rinku Singh", "India", "Left-hand finisher"),
        ("Ishan Kishan", "India", "Left-hand batter and wicketkeeper"), ("Prithvi Shaw", "India", "Right-hand opener"),
        ("Devdutt Padikkal", "India", "Left-hand top order"), ("Sai Sudharsan", "India", "Left-hand top order"),
        ("Abhishek Sharma", "India", "Left-hand opener"), ("Faf du Plessis", "South Africa", "Right-hand opener"),
        ("David Warner", "Australia", "Left-hand opener"), ("Jos Buttler", "England", "Right-hand opener and wicketkeeper"),
        ("Heinrich Klaasen", "South Africa", "Right-hand middle order and wicketkeeper"), ("Shimron Hetmyer", "West Indies", "Left-hand middle order"),
        ("Nicholas Pooran", "West Indies", "Left-hand batter and wicketkeeper"), ("Travis Head", "Australia", "Left-hand opener"),
        ("David Miller", "South Africa", "Left-hand finisher"), ("Kane Williamson", "New Zealand", "Right-hand top order"),
        ("Steve Smith", "Australia", "Right-hand top order"), ("Rachin Ravindra", "New Zealand", "Left-hand top order"),
        ("Phil Salt", "England", "Right-hand opener and wicketkeeper"), ("Jitesh Sharma", "India", "Right-hand batter and wicketkeeper"),
        ("Shahrukh Khan", "India", "Right-hand finisher"), ("Rahul Tripathi", "India", "Right-hand top order"),
        ("Dewald Brevis", "South Africa", "Right-hand middle order"), ("Prabhsimran Singh", "India", "Right-hand opener and wicketkeeper"),
    ],
    "Bowler": [
        ("Jasprit Bumrah", "India", "Right-arm fast"), ("Mohammed Shami", "India", "Right-arm fast"),
        ("Mohammed Siraj", "India", "Right-arm fast"), ("Arshdeep Singh", "India", "Left-arm fast"),
        ("Kuldeep Yadav", "India", "Left-arm wrist spin"), ("Yuzvendra Chahal", "India", "Leg spin"),
        ("Rashid Khan", "Afghanistan", "Leg spin"), ("Kagiso Rabada", "South Africa", "Right-arm fast"),
        ("Trent Boult", "New Zealand", "Left-arm fast"), ("Mitchell Starc", "Australia", "Left-arm fast"),
        ("Pat Cummins", "Australia", "Right-arm fast"), ("Anrich Nortje", "South Africa", "Right-arm fast"),
        ("Matheesha Pathirana", "Sri Lanka", "Right-arm fast"), ("Bhuvneshwar Kumar", "India", "Right-arm swing"),
        ("T Natarajan", "India", "Left-arm fast"), ("Avesh Khan", "India", "Right-arm fast"),
        ("Umran Malik", "India", "Right-arm fast"), ("Varun Chakravarthy", "India", "Mystery spin"),
        ("Ravi Bishnoi", "India", "Leg spin"), ("Noor Ahmad", "Afghanistan", "Left-arm wrist spin"),
        ("Adam Zampa", "Australia", "Leg spin"), ("Lockie Ferguson", "New Zealand", "Right-arm fast"),
        ("Josh Hazlewood", "Australia", "Right-arm fast"), ("Mark Wood", "England", "Right-arm fast"),
        ("Gerald Coetzee", "South Africa", "Right-arm fast"), ("Harshal Patel", "India", "Right-arm medium"),
        ("Mukesh Kumar", "India", "Right-arm medium"), ("Sandeep Sharma", "India", "Right-arm swing"),
        ("Mayank Yadav", "India", "Right-arm fast"), ("Wanindu Hasaranga", "Sri Lanka", "Leg spin"),
        ("Keshav Maharaj", "South Africa", "Left-arm orthodox spin"), ("Maheesh Theekshana", "Sri Lanka", "Off spin"),
        ("Reece Topley", "England", "Left-arm fast"),
    ],
    "All-rounder": [
        ("Hardik Pandya", "India", "Right-hand batter, right-arm fast"), ("Ravindra Jadeja", "India", "Left-hand batter, left-arm spin"),
        ("Axar Patel", "India", "Left-hand batter, left-arm spin"), ("Shivam Dube", "India", "Left-hand batter, right-arm medium"),
        ("Washington Sundar", "India", "Left-hand batter, off spin"), ("Nitish Kumar Reddy", "India", "Right-hand batter, right-arm medium"),
        ("Riyan Parag", "India", "Right-hand batter, leg spin"), ("Krunal Pandya", "India", "Left-hand batter, left-arm spin"),
        ("Vijay Shankar", "India", "Right-hand batter, right-arm medium"), ("Deepak Hooda", "India", "Right-hand batter, off spin"),
        ("Andre Russell", "West Indies", "Right-hand batter, right-arm fast"), ("Sunil Narine", "West Indies", "Left-hand batter, off spin"),
        ("Glenn Maxwell", "Australia", "Right-hand batter, off spin"), ("Cameron Green", "Australia", "Right-hand batter, right-arm fast"),
        ("Marcus Stoinis", "Australia", "Right-hand batter, right-arm medium"), ("Mitchell Marsh", "Australia", "Right-hand batter, right-arm medium"),
        ("Liam Livingstone", "England", "Right-hand batter, leg and off spin"), ("Sam Curran", "England", "Left-hand batter, left-arm fast"),
        ("Moeen Ali", "England", "Left-hand batter, off spin"), ("Ben Stokes", "England", "Left-hand batter, right-arm fast"),
        ("Sikandar Raza", "Zimbabwe", "Right-hand batter, off spin"), ("Mitchell Santner", "New Zealand", "Left-hand batter, left-arm spin"),
        ("Glenn Phillips", "New Zealand", "Right-hand batter, off spin"), ("Marco Jansen", "South Africa", "Left-hand batter, left-arm fast"),
        ("Aiden Markram", "South Africa", "Right-hand batter, off spin"), ("Romario Shepherd", "West Indies", "Right-hand batter, right-arm fast"),
        ("Jason Holder", "West Indies", "Right-hand batter, right-arm fast"), ("Azmatullah Omarzai", "Afghanistan", "Right-hand batter, right-arm fast"),
        ("Shakib Al Hasan", "Bangladesh", "Left-hand batter, left-arm spin"), ("Venkatesh Iyer", "India", "Left-hand batter, right-arm medium"),
        ("Rahul Tewatia", "India", "Left-hand batter, leg spin"), ("Abdul Samad", "India", "Right-hand batter, right-arm leg spin"),
        ("Anukul Roy", "India", "Left-hand batter, left-arm spin"),
    ],
}


def _build_roster() -> tuple[Player, ...]:
    players = []
    for role, entries in _ROSTERS.items():
        for name, country, style in entries:
            index = len(players)
            base_price = 200 if index < 12 else 100 if index < 28 else 50
            players.append(Player(index + 1, name, country, role, style, base_price))
    return tuple(players)


PLAYERS = _build_roster()
PLAYERS_BY_ID = {player.id: player for player in PLAYERS}


def public_player(player: Player) -> dict:
    return asdict(player)
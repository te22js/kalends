"""Screen-space reconstruction; attested sites, explicitly fictional microhistory."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PompeiiConfig:
    seed: int = 79
    horizon_days: int = 60
    memory_capacity: int = 32
    information_policy: str = "cautious"
    communication: bool = True

    def __post_init__(self):
        if type(self.seed) is not int or type(self.horizon_days) is not int or not 1 <= self.horizon_days <= 365:
            raise ValueError("seed must be an integer and horizon 1..365 days")
        if type(self.memory_capacity) is not int or not 4 <= self.memory_capacity <= 256:
            raise ValueError("memory capacity must be 4..256")
        if self.information_policy not in ("cautious", "credulous") or type(self.communication) is not bool:
            raise ValueError("invalid information policy")


LOCATIONS = [
    {"id":"bakery", "name":"Felix's bread counter", "x":650,"y":80,"w":320,"h":230,
     "door":{"x":810,"y":350},"kind":"bakery","interior":True,"source_id":"H19",
     "history_label":"Fictional bread counter. Bakeries are attested in Pompeii; this placement and business are invented."},
    {"id":"fullery", "name":"Fullonica of Stephanus", "x":220,"y":500,"w":330,"h":240,
     "door":{"x":385,"y":480},"kind":"fullery","interior":True,"source_id":"H04",
     "history_label":"Attested textile workshop I.6.7. The inhabitants and tasks in this game are fictional."},
    {"id":"thermopolium", "name":"Thermopolium of Vetutius Placidus", "x":1060,"y":500,"w":330,"h":240,
     "door":{"x":1225,"y":480},"kind":"thermopolium","interior":True,"source_id":"H05",
     "history_label":"Attested food counter I.8.8. Exact furnishings and daily dealings are reconstructed."},
    {"id":"household", "name":"House of the Menander", "x":570,"y":810,"w":400,"h":240,
     "door":{"x":770,"y":790},"kind":"household","interior":True,"source_id":"H06",
     "history_label":"Attested house I.10.4, reached by the local street network. This household story is fictional."},
    {"id":"water", "name":"The street fountain", "x":480,"y":385,"w":55,"h":50,
     "door":{"x":510,"y":415},"kind":"fountain","interior":False,"source_id":"H23",
     "history_label":"Pompeii had public water points; this exact position is a gameplay interpolation."},
    {"id":"forum_access", "name":"Road toward the forum", "x":15,"y":360,"w":90,"h":110,
     "door":{"x":90,"y":415},"kind":"street","interior":False,"source_id":"H03",
     "history_label":"Route marker only. The forum is not immediately beside this reconstructed block."}
]
STREETS = [{"x":0,"y":350,"w":1600,"h":130,"name":"Via dell'Abbondanza"},
           {"x":700,"y":480,"w":140,"h":330,"name":"Local street toward the household"}]
MAP = {"width":1600,"height":1100,"locations":LOCATIONS,"streets":STREETS,
       "bounds":{"x":0,"y":0,"w":1600,"h":1100},
       "disclaimer":"Schematic reconstruction, without surveyed distances. Attested places; fictional personal histories. 79 CE; exact eruption day debated."}
PEOPLE = {
    "Felix":{"role":"baker","location":"bakery","cash":28,"inventory":3,"social_position":"Fictional freedman running a bread counter","goal":"Keep flour for tomorrow's bread","caution":.7,"information_value":2},
    "Sabina":{"role":"food seller","location":"thermopolium","cash":26,"inventory":2,"social_position":"Fictional free woman managing a food counter","goal":"Feed customers without exhausting her working coins","caution":.45,"information_value":1},
    "Marcus":{"role":"trader","location":"street","cash":46,"inventory":6,"social_position":"Fictional free trader","goal":"Buy before scarcity and protect his margin","caution":.2,"information_value":3},
    "Chreste":{"role":"fullery worker","location":"fullery","cash":0,"inventory":0,"social_position":"Fictional enslaved worker; movement and paid work are constrained by the workshop","goal":"Complete workshop duties and maintain reliable help","caution":.7,"information_value":0},
    "Dama":{"role":"household messenger","location":"household","cash":0,"inventory":0,"social_position":"Fictional enslaved member of the household; not an independent merchant","goal":"Carry household reports and return to assigned duties","caution":.25,"information_value":0},
    "Lucius":{"role":"household steward","location":"household","cash":60,"inventory":5,"social_position":"Fictional freedman steward acting for a wealthy household","goal":"Secure household supplies and dependable service","caution":.85,"information_value":2}
}


def center(location):
    if location == "street":
        return (930, 415)
    place = next(p for p in LOCATIONS if p["id"] == location)
    return (place["x"] + place["w"] / 2, place["y"] + place["h"] * .65)

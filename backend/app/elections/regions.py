"""
FAZA 9 (dopuna) - mapiranje zupanije na NUTS2 statisticku regiju.

Izvor: sluzbena klasifikacija HR_NUTS 2021 (na snazi od 2022. za EU
kohezijsku politiku 2021-2027), potvrdjeno kroz sluzbenu EU state-aid
dokumentaciju (Europska komisija, DG Competition):
    HR02 Panonska Hrvatska  (8 zupanija)
    HR03 Jadranska Hrvatska (7 zupanija)
    HR05 Grad Zagreb        (posebna jedinica, dvojni grad+zupanija status)
    HR06 Sjeverna Hrvatska  (5 zupanija)
8 + 7 + 1 + 5 = 21 = tocan broj svih zupanijskih jedinica u RH (20
zupanija + Grad Zagreb).

Koristi se za grupiranje rezultata na Tally ekranu (zadatak #16 - graf po
zupaniji i graf po NUTS2 regiji) i za prikaz zupanije/regije uz svako
biracko mjesto (StationOut, zadatak #15).

Dijaspora ("Hrvati izvan Hrvatske") namjerno NIJE dio nijedne NUTS2 regije
niti zupanije - birači glasaju na DKP-ovima izvan teritorija RH. U ovoj
mapi ima svoj poseban marker kako bi grupiranje rezultata moglo Dijasporu
uvijek prikazati kao odvojenu kategoriju, nikad pribrojenu nekoj regiji.
"""

SJEVERNA_HRVATSKA = "Sjeverna Hrvatska"
PANONSKA_HRVATSKA = "Panonska Hrvatska"
JADRANSKA_HRVATSKA = "Jadranska Hrvatska"
GRAD_ZAGREB_REGIJA = "Grad Zagreb"
DIJASPORA = "Dijaspora"

# Redoslijed kojim se regije prikazuju na frontendu (zadatak #18).
NUTS2_REGIONS: list[str] = [
    SJEVERNA_HRVATSKA,
    PANONSKA_HRVATSKA,
    JADRANSKA_HRVATSKA,
    GRAD_ZAGREB_REGIJA,
    DIJASPORA,
]

_ZUPANIJA_TO_NUTS2: dict[str, str] = {
    # Sjeverna Hrvatska (5)
    "Zagrebačka županija": SJEVERNA_HRVATSKA,
    "Krapinsko-zagorska županija": SJEVERNA_HRVATSKA,
    "Varaždinska županija": SJEVERNA_HRVATSKA,
    "Koprivničko-križevačka županija": SJEVERNA_HRVATSKA,
    "Međimurska županija": SJEVERNA_HRVATSKA,
    # Panonska Hrvatska (8)
    "Sisačko-moslavačka županija": PANONSKA_HRVATSKA,
    "Karlovačka županija": PANONSKA_HRVATSKA,
    "Bjelovarsko-bilogorska županija": PANONSKA_HRVATSKA,
    "Virovitičko-podravska županija": PANONSKA_HRVATSKA,
    "Požeško-slavonska županija": PANONSKA_HRVATSKA,
    "Brodsko-posavska županija": PANONSKA_HRVATSKA,
    "Osječko-baranjska županija": PANONSKA_HRVATSKA,
    "Vukovarsko-srijemska županija": PANONSKA_HRVATSKA,
    # Jadranska Hrvatska (7)
    "Primorsko-goranska županija": JADRANSKA_HRVATSKA,
    "Ličko-senjska županija": JADRANSKA_HRVATSKA,
    "Zadarska županija": JADRANSKA_HRVATSKA,
    "Šibensko-kninska županija": JADRANSKA_HRVATSKA,
    "Splitsko-dalmatinska županija": JADRANSKA_HRVATSKA,
    "Istarska županija": JADRANSKA_HRVATSKA,
    "Dubrovačko-neretvanska županija": JADRANSKA_HRVATSKA,
    # Grad Zagreb (1) - posebna zupanijska i NUTS2 jedinica istovremeno
    "Grad Zagreb": GRAD_ZAGREB_REGIJA,
    # Dijaspora (1) - nije stvarna zupanija, ali dijeli isti "zupanija" stupac
    "Dijaspora": DIJASPORA,
}


def get_region(zupanija: str | None) -> str | None:
    """Vraca NUTS2 regiju (ili Dijaspora marker) za danu zupaniju.

    Vraca None ako zupanija nije popunjena ili nije prepoznata (npr.
    buduce rucno dodano biraliste s nestandardnim nazivom zupanije preko
    generickog bulk-importa) - frontend takve stanice prikazuje u posebnoj
    "Nepoznato" kategoriji umjesto da ih tiho izostavi iz grafa.
    """
    if zupanija is None:
        return None
    return _ZUPANIJA_TO_NUTS2.get(zupanija)


def all_zupanije() -> list[str]:
    """Popis svih prepoznatih zupanija (bez Dijaspora markera) - koristan
    frontendu za dropdown pri rucnom dodavanju/uredjivanju biralista."""
    return [z for z in _ZUPANIJA_TO_NUTS2 if z != DIJASPORA]

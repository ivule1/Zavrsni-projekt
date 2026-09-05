"""Faza 9 (dopuna) - dodaje polje zupanija na polling_stations + seed 129
biralista: 127 sluzbenih hrvatskih gradova (bez Zagreba, koji ima poseban
zupanijski status) + Grad Zagreb + jedan posebni unos "Hrvati izvan
Hrvatske" (dijaspora, glasa na DKP-ovima, ne pripada nijednoj zupaniji).

Izvor popisa gradova/zupanija: sluzbeni popis Ministarstva pravosudja i
uprave (mpudt.gov.hr) - "555 jedinica lokalne samouprave: 428 opcina i 127
gradova", plus Grad Zagreb kao posebna zupanijska jedinica.

registered_voters je namjerno placeholder (300 za svako biraliste), NE
stvaran popis biraca - vidi napomenu u PollingStation modelu.

Revision ID: d70a294c8d77
Revises: cb42997892de
Create Date: 2026-09-03
"""
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d70a294c8d77"
down_revision = "cb42997892de"
branch_labels = None
depends_on = None


# station_status je vec postojeci Postgres ENUM tip (kreiran ranijom
# migracijom uz PollingStation.status). create_type=False je BITAN - inace
# bi Alembic/SQLAlchemy pokusao ponovno kreirati tip koji vec postoji.
# Bez ovoga (tj. sa genericnim sa.String stupcem) psycopg3 driver salje
# vrijednost eksplicitno tipiziranu kao VARCHAR, pa Postgres odbija
# implicitni cast u enum ("column status is of type station_status but
# expression is of type character varying") - psycopg2 je to presutno
# tolerirao pa se greska nije pojavila u ranijoj (cloud) provjeri.
station_status_enum = postgresql.ENUM(
    "ACTIVE", "INACTIVE", name="station_status", create_type=False
)

polling_stations = sa.table(
    "polling_stations",
    sa.column("id", postgresql.UUID(as_uuid=True)),
    sa.column("code", sa.String),
    sa.column("name", sa.String),
    sa.column("location", sa.String),
    sa.column("zupanija", sa.String),
    sa.column("registered_voters", sa.Integer),
    sa.column("status", station_status_enum),
)

# 127 sluzbenih gradova + Grad Zagreb + dijaspora = 129 redaka
SEED_ROWS = [
    {"id": uuid.UUID('696d82f7-bee5-42e1-9905-e78e8d451b43'), "code": 'DUGO-SELO', "name": 'Dugo Selo', "zupanija": 'Zagrebačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('549bc372-7066-4f19-ab33-27680251622c'), "code": 'IVANIC-GRAD', "name": 'Ivanić-Grad', "zupanija": 'Zagrebačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('6bd45dce-dcc7-4b60-b6b3-f96f66240cbb'), "code": 'JASTREBARSKO', "name": 'Jastrebarsko', "zupanija": 'Zagrebačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('74bf8dc8-b2b6-4605-8a9e-fac3381e3a99'), "code": 'SAMOBOR', "name": 'Samobor', "zupanija": 'Zagrebačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('0ca4d866-1010-4323-948f-5f0ae38ae54b'), "code": 'SVETA-NEDELJA', "name": 'Sveta Nedelja', "zupanija": 'Zagrebačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('ca5ceba5-210b-4fe1-933b-f95be2339dcd'), "code": 'SVETI-IVAN-ZELINA', "name": 'Sveti Ivan Zelina', "zupanija": 'Zagrebačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('393e85d8-dfea-4cb0-a649-b78bd8d7bb91'), "code": 'VELIKA-GORICA', "name": 'Velika Gorica', "zupanija": 'Zagrebačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('58e51d73-a47c-44c4-9ca0-73996d41e11a'), "code": 'VRBOVEC', "name": 'Vrbovec', "zupanija": 'Zagrebačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('625b761b-4178-4df6-a49e-02626102113e'), "code": 'ZAPRESIC', "name": 'Zaprešić', "zupanija": 'Zagrebačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('641b4140-4efc-4a93-9a4f-d3bea94b72dd'), "code": 'DONJA-STUBICA', "name": 'Donja Stubica', "zupanija": 'Krapinsko-zagorska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('abe84fcf-ebcf-4c65-9df1-a530d4df70d8'), "code": 'KLANJEC', "name": 'Klanjec', "zupanija": 'Krapinsko-zagorska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('cfbfb6f9-56f9-494a-a0b5-22bfb30e09bc'), "code": 'KRAPINA', "name": 'Krapina', "zupanija": 'Krapinsko-zagorska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('3ef99e94-06b5-4e9c-b872-5987d44eded9'), "code": 'OROSLAVJE', "name": 'Oroslavje', "zupanija": 'Krapinsko-zagorska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('8687e383-dcd6-4c0d-95f5-727bba0a238e'), "code": 'PREGRADA', "name": 'Pregrada', "zupanija": 'Krapinsko-zagorska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('01006e50-bf49-45b3-bd6a-64c87a034a5a'), "code": 'ZABOK', "name": 'Zabok', "zupanija": 'Krapinsko-zagorska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('0274afbf-efaa-449d-b758-006a1d3ab16e'), "code": 'ZLATAR', "name": 'Zlatar', "zupanija": 'Krapinsko-zagorska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('82af3c36-1d67-4ccf-9cd5-28133c51f011'), "code": 'GLINA', "name": 'Glina', "zupanija": 'Sisačko-moslavačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('7bc9ed9e-a61a-4012-8301-2ddcb0069817'), "code": 'HRVATSKA-KOSTAJNICA', "name": 'Hrvatska Kostajnica', "zupanija": 'Sisačko-moslavačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('bc884a72-adbd-4a66-857e-10ee7c999956'), "code": 'KUTINA', "name": 'Kutina', "zupanija": 'Sisačko-moslavačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('e91dfb66-0bd3-4618-ae23-2e167120e19e'), "code": 'NOVSKA', "name": 'Novska', "zupanija": 'Sisačko-moslavačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('003c7d29-0d2c-41a4-90e6-3a049689deec'), "code": 'PETRINJA', "name": 'Petrinja', "zupanija": 'Sisačko-moslavačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('e536e088-d3a3-49f3-bfed-890a02a3d825'), "code": 'POPOVACA', "name": 'Popovača', "zupanija": 'Sisačko-moslavačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('1114fb16-db46-42d2-a438-e953ed65b27f'), "code": 'SISAK', "name": 'Sisak', "zupanija": 'Sisačko-moslavačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('5b3d4737-cda3-45b1-ac2c-78f3b563f848'), "code": 'DUGA-RESA', "name": 'Duga Resa', "zupanija": 'Karlovačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('7e4515aa-8e86-4adc-8978-3ca1e2a5c118'), "code": 'KARLOVAC', "name": 'Karlovac', "zupanija": 'Karlovačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('f5db4632-0db1-4fbf-b695-fc15fc544e55'), "code": 'OGULIN', "name": 'Ogulin', "zupanija": 'Karlovačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('a0e936eb-decc-46f6-93a7-41c8954e0b76'), "code": 'OZALJ', "name": 'Ozalj', "zupanija": 'Karlovačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('4dd8ed58-fe31-4749-a740-b519301e1d3d'), "code": 'SLUNJ', "name": 'Slunj', "zupanija": 'Karlovačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('dabce0e7-5c10-43ba-a8de-705df2ad5b58'), "code": 'IVANEC', "name": 'Ivanec', "zupanija": 'Varaždinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('ca1930c7-6249-4edb-8dca-83cdfcad9b75'), "code": 'LEPOGLAVA', "name": 'Lepoglava', "zupanija": 'Varaždinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('a73d4065-3d94-45ba-84b3-1362a8b2159a'), "code": 'LUDBREG', "name": 'Ludbreg', "zupanija": 'Varaždinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('fe9e2a1d-90f8-44d6-9506-1d193f1c268f'), "code": 'NOVI-MAROF', "name": 'Novi Marof', "zupanija": 'Varaždinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('6dd993c7-4958-49b0-90de-e3d1d81ec648'), "code": 'VARAZDIN', "name": 'Varaždin', "zupanija": 'Varaždinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('207fef27-992c-4f2d-8095-fc7689f8ba0b'), "code": 'VARAZDINSKE-TOPLICE', "name": 'Varaždinske Toplice', "zupanija": 'Varaždinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('f68dfaa0-7079-4040-baeb-5cf9371d8251'), "code": 'KOPRIVNICA', "name": 'Koprivnica', "zupanija": 'Koprivničko-križevačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('80baf187-0633-4fee-b0e3-831cdb6d99fc'), "code": 'KRIZEVCI', "name": 'Križevci', "zupanija": 'Koprivničko-križevačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('d3a9d6ab-102e-4935-9de3-305c11f8f961'), "code": 'DJURDJEVAC', "name": 'Đurđevac', "zupanija": 'Koprivničko-križevačka županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('b05d1d83-adc7-42fd-8c2c-d0b3d95f2baf'), "code": 'BJELOVAR', "name": 'Bjelovar', "zupanija": 'Bjelovarsko-bilogorska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('8162d88f-d600-4709-9a37-430244a1836a'), "code": 'CAZMA', "name": 'Čazma', "zupanija": 'Bjelovarsko-bilogorska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('a32cdf93-e7c8-4e4c-a75b-ff5de797c7e1'), "code": 'DARUVAR', "name": 'Daruvar', "zupanija": 'Bjelovarsko-bilogorska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('72a3a00f-3989-44c2-8a57-47da03d409b0'), "code": 'GARESNICA', "name": 'Garešnica', "zupanija": 'Bjelovarsko-bilogorska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('2580cf91-7670-4bdb-9417-51cbe88ef6cd'), "code": 'GRUBISNO-POLJE', "name": 'Grubišno Polje', "zupanija": 'Bjelovarsko-bilogorska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('a35096bd-308b-4af3-bd56-41de727b69d7'), "code": 'BAKAR', "name": 'Bakar', "zupanija": 'Primorsko-goranska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('aaceed84-4b07-498d-ba90-c01d8d9ba0ac'), "code": 'CRES', "name": 'Cres', "zupanija": 'Primorsko-goranska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('dfda511f-680c-4898-8b50-f0302b4b8e4c'), "code": 'CRIKVENICA', "name": 'Crikvenica', "zupanija": 'Primorsko-goranska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('2989e290-c4bc-4599-8b01-7887182d90f1'), "code": 'CABAR', "name": 'Čabar', "zupanija": 'Primorsko-goranska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('a86f2209-edd4-4e72-b968-bfe24b3a48b9'), "code": 'DELNICE', "name": 'Delnice', "zupanija": 'Primorsko-goranska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('69245543-34fa-425a-8fbe-f5a3aeec887b'), "code": 'KASTAV', "name": 'Kastav', "zupanija": 'Primorsko-goranska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('440690d0-c1e0-4c34-b06a-8c348739da33'), "code": 'KRALJEVICA', "name": 'Kraljevica', "zupanija": 'Primorsko-goranska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('6fcb3260-3161-44bd-a102-7e15c9121e44'), "code": 'KRK', "name": 'Krk', "zupanija": 'Primorsko-goranska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('84fdd914-0847-4461-855b-1f3df6029a91'), "code": 'MALI-LOSINJ', "name": 'Mali Lošinj', "zupanija": 'Primorsko-goranska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('c079da67-3df7-4d0d-907d-2f0e693d7898'), "code": 'NOVI-VINODOLSKI', "name": 'Novi Vinodolski', "zupanija": 'Primorsko-goranska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('3e4dcc7f-52d0-42eb-872e-0ab93f7b4019'), "code": 'OPATIJA', "name": 'Opatija', "zupanija": 'Primorsko-goranska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('53c8d09a-943b-40fb-b6ce-5325a482516b'), "code": 'RAB', "name": 'Rab', "zupanija": 'Primorsko-goranska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('2e695826-f23d-4dfd-bd18-4d6f23c2b4af'), "code": 'RIJEKA', "name": 'Rijeka', "zupanija": 'Primorsko-goranska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('717881da-42ab-45c1-be5d-21bab0c4c501'), "code": 'VRBOVSKO', "name": 'Vrbovsko', "zupanija": 'Primorsko-goranska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('9b9be413-132c-4228-ad74-ee9f9ae85050'), "code": 'GOSPIC', "name": 'Gospić', "zupanija": 'Ličko-senjska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('41277975-ca54-437c-b71e-035b00a6e42e'), "code": 'NOVALJA', "name": 'Novalja', "zupanija": 'Ličko-senjska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('c99965bb-df65-4dd2-bde8-c0d31f61ce0d'), "code": 'OTOCAC', "name": 'Otočac', "zupanija": 'Ličko-senjska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('105ac66b-520f-4da6-979f-49d4eb36b073'), "code": 'SENJ', "name": 'Senj', "zupanija": 'Ličko-senjska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('9388175e-97d3-4c9a-869c-4077167ffc38'), "code": 'ORAHOVICA', "name": 'Orahovica', "zupanija": 'Virovitičko-podravska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('a89c2d0b-5271-4930-81e6-44a19877384d'), "code": 'SLATINA', "name": 'Slatina', "zupanija": 'Virovitičko-podravska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('266fa1df-eb50-4b08-acd0-3f7b3a6e6fae'), "code": 'VIROVITICA', "name": 'Virovitica', "zupanija": 'Virovitičko-podravska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('ad4882c6-283a-4e7a-a204-f1204def3ec5'), "code": 'KUTJEVO', "name": 'Kutjevo', "zupanija": 'Požeško-slavonska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('a0af5838-359a-43b3-bd79-284e452d6c83'), "code": 'LIPIK', "name": 'Lipik', "zupanija": 'Požeško-slavonska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('d8b33d90-d423-4713-88ff-84f2f259f81a'), "code": 'PAKRAC', "name": 'Pakrac', "zupanija": 'Požeško-slavonska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('1a31fe38-3ed6-4507-91aa-7cd7714e5d8a'), "code": 'PLETERNICA', "name": 'Pleternica', "zupanija": 'Požeško-slavonska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('441ed6b1-ca20-4465-88a2-65b3cb950bc8'), "code": 'POZEGA', "name": 'Požega', "zupanija": 'Požeško-slavonska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('e0fe2ec7-2e81-413f-a0ea-4b6097cd1b62'), "code": 'NOVA-GRADISKA', "name": 'Nova Gradiška', "zupanija": 'Brodsko-posavska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('44f28c79-86a5-413c-81ed-b80f85abbd4a'), "code": 'SLAVONSKI-BROD', "name": 'Slavonski Brod', "zupanija": 'Brodsko-posavska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('74c6aad2-a20c-462a-a2d7-5edc6991a852'), "code": 'BENKOVAC', "name": 'Benkovac', "zupanija": 'Zadarska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('b920f786-991a-499f-8f9a-cd689707be5b'), "code": 'BIOGRAD-NA-MORU', "name": 'Biograd na Moru', "zupanija": 'Zadarska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('7c88913b-6e6b-4078-a292-f38d1d09b754'), "code": 'NIN', "name": 'Nin', "zupanija": 'Zadarska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('c6867b7b-e200-4585-b081-682ed6c2a0da'), "code": 'OBROVAC', "name": 'Obrovac', "zupanija": 'Zadarska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('4ef02b26-a2b1-4b69-b1e8-47bd3d4b0395'), "code": 'PAG', "name": 'Pag', "zupanija": 'Zadarska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('9a4e8053-d836-4050-bff0-6a1796ede152'), "code": 'ZADAR', "name": 'Zadar', "zupanija": 'Zadarska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('a1b6d465-9df1-4fd2-9ab2-3ce15c0b5992'), "code": 'BELI-MANASTIR', "name": 'Beli Manastir', "zupanija": 'Osječko-baranjska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('34f42b53-ea59-4b84-b67c-f22f4ff70158'), "code": 'BELISCE', "name": 'Belišće', "zupanija": 'Osječko-baranjska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('7a1dcc3f-b9af-4083-b8a7-5427fe6bef8a'), "code": 'DONJI-MIHOLJAC', "name": 'Donji Miholjac', "zupanija": 'Osječko-baranjska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('9131e4c6-d69d-4e3c-86d7-125f3201f66b'), "code": 'DJAKOVO', "name": 'Đakovo', "zupanija": 'Osječko-baranjska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('3fdf6fe4-3f15-443d-a9c6-96e65fc98769'), "code": 'NASICE', "name": 'Našice', "zupanija": 'Osječko-baranjska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('ec763ef3-b55b-409b-98d1-d16d9ef867d8'), "code": 'OSIJEK', "name": 'Osijek', "zupanija": 'Osječko-baranjska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('b4829c67-9152-44e0-83be-d62b403b74ce'), "code": 'VALPOVO', "name": 'Valpovo', "zupanija": 'Osječko-baranjska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('8d3357a9-3379-45c2-9e75-e6a3459358c4'), "code": 'DRNIS', "name": 'Drniš', "zupanija": 'Šibensko-kninska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('109e096a-415f-4756-a690-32cd5b00fd70'), "code": 'KNIN', "name": 'Knin', "zupanija": 'Šibensko-kninska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('97bfe294-17f2-448e-9ca3-5b14ff3ca250'), "code": 'SKRADIN', "name": 'Skradin', "zupanija": 'Šibensko-kninska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('a06fe4ee-a4ac-462d-ac8d-b4918bdae358'), "code": 'SIBENIK', "name": 'Šibenik', "zupanija": 'Šibensko-kninska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('91d2acac-5885-4abc-b626-939738454edc'), "code": 'VODICE', "name": 'Vodice', "zupanija": 'Šibensko-kninska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('b9dbf3e5-8975-40c4-b5dd-8a17fdd37703'), "code": 'ILOK', "name": 'Ilok', "zupanija": 'Vukovarsko-srijemska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('c58a4124-0172-4b0e-b545-4ff728d0e4ce'), "code": 'OTOK', "name": 'Otok', "zupanija": 'Vukovarsko-srijemska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('122cbab9-e208-473d-b98d-d91219cc2031'), "code": 'VINKOVCI', "name": 'Vinkovci', "zupanija": 'Vukovarsko-srijemska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('e7d9fb84-3196-49b6-8253-a40d16eea24e'), "code": 'VUKOVAR', "name": 'Vukovar', "zupanija": 'Vukovarsko-srijemska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('4f532bd0-59fd-406b-aed3-06684d4f6377'), "code": 'ZUPANJA', "name": 'Županja', "zupanija": 'Vukovarsko-srijemska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('11052ed8-832c-4813-9a06-eca75a26976e'), "code": 'HVAR', "name": 'Hvar', "zupanija": 'Splitsko-dalmatinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('800cd9ae-8927-4ce5-a674-ae43ec600ed4'), "code": 'IMOTSKI', "name": 'Imotski', "zupanija": 'Splitsko-dalmatinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('c344b819-e7db-48f3-8f5e-ddd08d293516'), "code": 'KASTELA', "name": 'Kaštela', "zupanija": 'Splitsko-dalmatinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('3671cadc-c74e-4188-bc44-6c049ca3226e'), "code": 'KOMIZA', "name": 'Komiža', "zupanija": 'Splitsko-dalmatinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('da89d6c5-e820-47b4-96de-e158ac937d8c'), "code": 'MAKARSKA', "name": 'Makarska', "zupanija": 'Splitsko-dalmatinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('ccd193f1-24fe-4031-880f-4e61bab2ce2c'), "code": 'OMIS', "name": 'Omiš', "zupanija": 'Splitsko-dalmatinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('79e38f38-8c6d-4c16-9982-bf2019c38353'), "code": 'SINJ', "name": 'Sinj', "zupanija": 'Splitsko-dalmatinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('3191ddfa-7213-4729-bffa-58a90c1d83dc'), "code": 'SOLIN', "name": 'Solin', "zupanija": 'Splitsko-dalmatinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('4e965bb6-e706-4878-85e4-f60e0e72e542'), "code": 'SPLIT', "name": 'Split', "zupanija": 'Splitsko-dalmatinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('da980b74-c3b8-4025-8daa-e01d129cfb10'), "code": 'STARI-GRAD', "name": 'Stari Grad', "zupanija": 'Splitsko-dalmatinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('8f3884eb-db2f-45d8-936f-261324975178'), "code": 'SUPETAR', "name": 'Supetar', "zupanija": 'Splitsko-dalmatinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('92551054-a236-49ff-aefc-371292447139'), "code": 'TRILJ', "name": 'Trilj', "zupanija": 'Splitsko-dalmatinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('c3142301-122a-4343-b0bd-6ac541b8e068'), "code": 'TROGIR', "name": 'Trogir', "zupanija": 'Splitsko-dalmatinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('0efbadcd-e8ef-485e-be5f-67bbb3885dbc'), "code": 'VIS', "name": 'Vis', "zupanija": 'Splitsko-dalmatinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('a4a1d199-1e8a-4b99-a645-6ad74a49fd62'), "code": 'VRGORAC', "name": 'Vrgorac', "zupanija": 'Splitsko-dalmatinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('3853dc04-c298-4cda-858e-dba7009cdfc3'), "code": 'VRLIKA', "name": 'Vrlika', "zupanija": 'Splitsko-dalmatinska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('4ae4ea64-11c6-4f66-9821-327e623b7301'), "code": 'BUJE', "name": 'Buje', "zupanija": 'Istarska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('5dd5811f-1015-472c-8b8d-ad4362b90867'), "code": 'BUZET', "name": 'Buzet', "zupanija": 'Istarska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('2d848635-4858-4907-b8db-c711c764da9c'), "code": 'LABIN', "name": 'Labin', "zupanija": 'Istarska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('e272a71f-4c32-4973-aa8e-a973fcdd0e0e'), "code": 'NOVIGRAD', "name": 'Novigrad', "zupanija": 'Istarska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('f062c9d0-677c-4329-aecd-2514413568fe'), "code": 'PAZIN', "name": 'Pazin', "zupanija": 'Istarska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('ecf85122-8659-433a-8c4d-23b20dfb1e1e'), "code": 'POREC', "name": 'Poreč', "zupanija": 'Istarska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('2b5456a5-b9d9-426a-a791-a023c0dba77c'), "code": 'PULA', "name": 'Pula', "zupanija": 'Istarska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('bff6f2a5-408e-4bdd-a117-10dac97e7cae'), "code": 'ROVINJ', "name": 'Rovinj', "zupanija": 'Istarska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('20c61273-0236-45db-8d27-fd12833242b6'), "code": 'UMAG', "name": 'Umag', "zupanija": 'Istarska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('409b7420-7043-4c87-89fb-2d474bc09527'), "code": 'VODNJAN', "name": 'Vodnjan', "zupanija": 'Istarska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('a65da26b-71b9-4a9c-9e12-817d953cd18c'), "code": 'DUBROVNIK', "name": 'Dubrovnik', "zupanija": 'Dubrovačko-neretvanska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('1302e17f-9d2a-4ab6-a32f-814b057e6401'), "code": 'KORCULA', "name": 'Korčula', "zupanija": 'Dubrovačko-neretvanska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('9e26cdfa-9ed3-4b4e-9215-3b428651dee1'), "code": 'METKOVIC', "name": 'Metković', "zupanija": 'Dubrovačko-neretvanska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('efcdb5ef-c1f5-4cdb-9d89-e9f02a571079'), "code": 'OPUZEN', "name": 'Opuzen', "zupanija": 'Dubrovačko-neretvanska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('c10dd4d3-50c0-4f5c-8719-4e7065332086'), "code": 'PLOCE', "name": 'Ploče', "zupanija": 'Dubrovačko-neretvanska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('5c3bdaee-db7a-488c-a3c9-8bd0c9bd5382'), "code": 'CAKOVEC', "name": 'Čakovec', "zupanija": 'Međimurska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('9ae9f5d6-7d92-477c-b22f-68878fddee0d'), "code": 'MURSKO-SREDISCE', "name": 'Mursko Središće', "zupanija": 'Međimurska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('932d0bcf-d10e-49a2-8763-e8e897bb1cdd'), "code": 'PRELOG', "name": 'Prelog', "zupanija": 'Međimurska županija', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('84b17a87-b148-42d5-8a1c-35acba358b19'), "code": 'ZAGREB', "name": 'Zagreb', "zupanija": 'Grad Zagreb', "registered_voters": 300, "status": "ACTIVE"},
    {"id": uuid.UUID('542ec616-6bf4-45c1-9daf-9fe3707ba863'), "code": 'HRVATI-IZVAN-HRVATSKE', "name": 'Hrvati izvan Hrvatske', "zupanija": 'Dijaspora', "registered_voters": 300, "status": "ACTIVE"},]


def upgrade() -> None:
    op.add_column(
        "polling_stations",
        sa.Column("zupanija", sa.String(length=100), nullable=True),
    )

    op.bulk_insert(polling_stations, SEED_ROWS)


def downgrade() -> None:
    codes = [row["code"] for row in SEED_ROWS]
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM polling_stations WHERE code = ANY(:codes)"),
        {"codes": codes},
    )
    op.drop_column("polling_stations", "zupanija")

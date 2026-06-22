Herzlich Willkommen im Repository von coohjaay aka Rieke Meißner!

Hier eine kurze Erklärung, wie die Umgebung eingerichtet wird und was es sonst noch spannendes zu entdecken gibt.

## Projekt

Dieses Repo enthält eine Analyse der offenen Einsatzdaten der Berliner Feuerwehr mit Fokus auf die Hilfsfrist (Eintreffzeit der Rettungskräfte). Darauf aufbauend gibt es eine interaktive Streamlit-App (`app.py`), die für Bezirk und Dringlichkeitsstufe die historische Hilfsfrist-Quote sowie eine modellbasierte Vorhersage der Eintreffzeit anzeigt.

## Repo klonen

```
git clone https://github.com/coohjaay/BigdataNeu
cd BigdataNeu
```

## Setup

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Daten besorgen

**Standard (empfohlen):** Lädt nur die Daten, die das Notebook tatsächlich braucht (ca. 650 MB).
```
./setup_for_data.sh
```

**Alternative:** Falls du dir das komplette BF-Open-Data-Repo anschauen willst, kannst du es auch komplett klonen. ACHTUNG! Das Repo ist sehr groß (über 6 GB), der Download kann 30+ Minuten dauern.
```
git clone https://github.com/Berliner-Feuerwehr/BF-Open-Data data/BF-Open-Data
```

## Notebook ausführen
ACHTUNG! Das Ausführen des Notebooks kann auch bis zu 15 Minuten dauern!
```
jupyter lab
```

Im Browser `sample.ipynb` öffnen und über "Run All" komplett durchlaufen lassen. Das Training der Modelle und das Einlesen der CSVs kann je nach Rechner einige Minuten dauern.

## App 

Die App ist unter http://187.124.190.185:8501/ erreichbar.

Falls die Seite nicht erreichbar ist, kann sie wie folgt lokal nachgebaut werden:

```
docker compose up -d --build
```

Danach ist sie unter http://localhost:8501 erreichbar.
# 🎴 Analitzador de Rangs i Probabilitats de Pòquer (estil Flopzilla)

Aplicació web **local** per analitzar la força del **rang del rival** contra un board
determinat (flop, turn o river). No cal introduir cap mà pròpia: l'eina desglossa el
percentatge de combos del rang rival que tenen cada categoria de mà (Quads, Full House,
Flush, Escala, Top Pair, Mid Pair, Overpair, As Alt, etc.) així com els projectes
(draws: FD, OESD, Gutshot, Backdoor FD/SD).

---

## 📋 Requisits del sistema

| Component | Versió mínima | Notes |
|---|---|---|
| Python | 3.10+ | Comprova amb `python --version` |
| pip | qualsevol recent | Gestor de paquets de Python |

Dependències (veure `requirements.txt`):

- **FastAPI** ≥ 0.104.1 — API REST
- **Uvicorn** ≥ 0.24.0 — servidor ASGI
- **treys** ≥ 0.1.8 — avaluador exacte de mans de pòquer
- **Pydantic** ≥ 2.0 — validació de models

No cal cap connexió a Internet un cop instal·lades les dependències: tot és local.

---

## 📂 Estructura de directoris

```
poker-range-analyzer/
├── README.md               ← aquest fitxer
├── requirements.txt        ← dependències Python
├── run.py                  ← punt d'entrada (llança Uvicorn)
├── backend/
│   ├── __init__.py
│   ├── main.py             ← aplicació FastAPI (rutes / i /api/analyze)
│   ├── models.py           ← models Pydantic (petició/resposta)
│   ├── range_parser.py     ← parser de rangs (graella 13×13 + notació "AA+", "AKs+"…)
│   └── range_analyzer.py   ← motor d'anàlisi amb treys (classificació i % de combos)
└── frontend/
    └── index.html          ← interfície única (HTML5 + Vanilla JS + CSS tema fosc)
```

---

## 🚀 Instal·lació

Tens **dues opcions** per instal·lar les dependències. Tries-ne una; no cal
executar les dues. Abans de qualsevol opció, comprova que tens Python 3.10 o
superior:

```bash
python --version      # Windows
python3 --version     # Linux / macOS
```

Si la versió és inferior a 3.10, actualitza Python des de https://www.python.org/downloads/
(important: a Windows, marca la casella **"Add Python to PATH"** durant la instal·lació).

---

### Opció A — Entorn virtual (recomanada)

Un **entorn virtual** (`venv`) és una carpeta aïllada on s'instal·len les
dependències d'aquest projecte sense tocar el Python global del sistema.
Avantatges:

- Evita conflictes de versions amb altres projectes Python que tinguis.
- Si demà canvia una dependència, només afectarà aquest projecte.
- Pots esborrar-ho tot simplement eliminant la carpeta `.venv`.

#### A.1 — Linux / macOS (bash o zsh)

**Pas 1 — Situa't a l'arrel del projecte:**

```bash
cd <arrel-del-projecte>    # p. ex. cd poker-range-analyzer
```

**Pas 2 — Crea l'entorn virtual** (es crearà una carpeta oculta anomenada `.venv`):

```bash
python3 -m venv .venv
```

> Si dona error `ensurepip is not available`, instal·la el paquet del sistema:
> Debian/Ubuntu: `sudo apt install python3-venv` · Fedora: `sudo dnf install python3-virtualenv` ·
> macOS (Homebrew): `brew install python@3.12`

**Pas 3 — Activa l'entorn:**

```bash
source .venv/bin/activate
```

A partir d'aquí veuràs el prefix `(.venv)` al costat del prompt de la terminal:

```
(.venv) $
```

Mentre el prefix sigui visible, ordres com `python` o `pip` apunten a l'entorn
aïllat i no al sistema global.

**Pas 4 — Instal·la les dependències dins l'entorn:**

```bash
pip install --upgrade pip        # (opcional) actualitza pip primer
pip install -r requirements.txt
```

Sortida esperada (resum):

```
Collecting fastapi>=0.104.1
Collecting uvicorn>=0.24.0
Collecting treys>=0.1.8
Collecting pydantic>=2.0
...
Successfully installed annotated-types-... fastapi-... pydantic-... starlette-... treys-0.1.8 uvicorn-...
```

(Verificat: `pip list` mostra `fastapi`, `uvicorn`, `treys 0.1.8` i `pydantic`.)

**Pas 5 — Verifica la instal·lació:**

```bash
pip list | grep -E "fastapi|uvicorn|treys|pydantic"
python -c "import fastapi, uvicorn, treys, pydantic; print('OK')"
```

Si mostra `OK`, ja pots passar a la secció **▶️ Execució**.

**Quan hagis acabat de treballar**, desactiva l'entorn amb:

```bash
deactivate
```

> Cada vegada que obris una terminal nova per treballar en aquest projecte,
> només cal repetir el **Pas 3** (`source .venv/bin/activate`); els Passos 2 i 4
> ja no cal repetir-los perquè la carpeta `.venv` conserva les dependències.

#### A.2 — Windows (PowerShell)

**Pas 1 — Situa't a l'arrel del projecte:**

```powershell
cd <arrel-del-projecte>    # p. ex. cd poker-range-analyzer
```

**Pas 2 — Crea l'entorn virtual:**

```powershell
python -m venv .venv
```

**Pas 3 — Activa l'entorn:**

```powershell
.venv\Scripts\Activate.ps1
```

Si PowerShell bloqueja l'script amb un error d'*execution policy*, executa una
vegada (només cal fer-ho un cop a l'equip):

```powershell
Set-ExecutionPolicy -Scope CurrentUser ExecutionPolicy RemoteSigned
```

o bé activa'l només per a la sessió actual:

```powershell
powershell -ExecutionPolicy Bypass -Command "& {.venv\Scripts\Activate.ps1}"
```

Si uses **Símbol del sistema (cmd.exe)** en lloc de PowerShell, l'activació és:

```cmd
.venv\Scripts\activate.bat
```

Amb l'entorn actiu veuràs `(.venv)` al prompt:

```
(.venv) PS C:\...\poker-range-analyzer>
```

**Pas 4 — Instal·la les dependències:**

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

**Pas 5 — Verifica:**

```powershell
pip list
python -c "import fastapi, uvicorn, treys, pydantic; print('OK')"
```

Per desactivar l'entorn: `deactivate`.

---

### Opció B — Instal·lació global (sense venv)

Instal·la les dependències directament al Python del sistema. És més ràpid i
més senzill, però **les versions compartiran espai amb qualsevol altre projecte
Python que tinguis**; si un altre projecte necessita una versió diferent de
FastAPI o Pydantic, es poden trepitjar. Recomanable només si aquest serà el teu
únic projecte Python o si saps el que fas.

#### B.1 — Comprovació prèvia d'integritat

Assegura't que `pip` apunta al mateix Python que farà servir el servidor:

```bash
python -m pip --version
# Sortida: "pip x.x from /ruta/al/python/site-packages/pip (python 3.1x)"
```

La ruta indicada ha de correspondre al Python que vols utilitzar. En cas de dubte,
**utilitza sempre la forma `python -m pip`** (o `python3 -m pip` a Linux/macOS)
en lloc de `pip` a seques: això garanteix que la instal·lació va al
intèrpret correcte.

#### B.2 — Instal·lació

**Linux / macOS:**

```bash
cd <arrel-del-projecte>
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

**Windows:**

```powershell
cd <arrel-del-projecte>
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Si el sistema et demana permisos o es queixa de *"externally-managed-environment"*
(distribucions Linux modernes basades en PEP 668), afegeix la bandera
`--user` per instal·lar només per al teu usuari:

```bash
python3 -m pip install --user -r requirements.txt
```

(O bé, en últim extrem i sota el teu risc: `--break-system-packages`).

#### B.3 — Verificació

```bash
python3 -m pip show fastapi uvicorn treys pydantic
python3 -c "import fastapi, uvicorn, treys, pydantic; print('OK')"
```

#### B.4 — Actualitzacions i desinstal·lació

Actualitzar les dependències a les últimes versions compatibles:

```bash
python3 -m pip install -r requirements.txt --upgrade
```

Desinstal·lar tot el que s'ha instal·lat per aquesta via:

```bash
python3 -m pip uninstall -y fastapi uvicorn treys pydantic starlette anyio annotated-types h11 click
```

> ⚠️ Aquesta desinstal·lació global afectarà també qualsevol altre projecte que
> faci servir aquests paquets. Per això l'Opció A és la recomanada.

---

### Quina opció triar?

| Criteri | Opció A (venv) | Opció B (global) |
|---|---|---|
| Aïllament entre projectes | ✅ Sí | ❌ No |
| Facilitat inicial | Mitjana (cal activar el venv cada sessió) | Alta (una sola ordre) |
| Desinstal·lació neta | ✅ Esborra `.venv` i punt | ⚠️ Uninstall global arriscat |
| Entorns restringits corporatius | ✅ Sol funcionar | ❌ Pot bloquejar `pip` global |
| Requisit per executar el projecte | Activa el venv abans de `python run.py` | Cap pas addicional |

Recorda: **si tries l'Opció A, activa el venv abans d'executar `python run.py`**
(altrament obtindràs `ModuleNotFoundError: No module named 'fastapi'`).

---

## ▶️ Execució

Des de l'arrel del projecte (`poker-range-analyzer/`):

```bash
python run.py
```

Això arrenca Uvicorn amb **recàrrega automàtica** (mode desenvolupament) a:

```
http://127.0.0.1:8000
```

Obre aquesta URL al navegador i veuràs la interfície completa.

Alternativa manual (sense `run.py`):

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Per aturar el servidor: `Ctrl+C` a la terminal.

> Si el port 8000 està ocupat, edita `run.py` i canvia `port=8000` per un altre
> (per exemple `port=8080`) i accedeix a `http://127.0.0.1:8080`.

---

## 🖱️ Com utilitzar la interfície

1. **Rang del rival**: fes clic sobre les cel·les de la graella **13×13** per
   activar/desactivar combos.
   - Diagonal → parells (AA, KK, …) — color vermellós
   - Triangular superior → suited (AKs, QJs, …) — color verdós
   - Triangular inferior → offsuit (AKo, QJo, …) — color gris
   - El comptador de combos seleccionats s'actualitza en temps real.
   - També pots escriure un rang en format text (p. ex. `AA+, AKs+, QQ, 77, KTs`) al
     camp d'input manual.
2. **Board**: introdueix les cartes comunitàries als slots gràfics (clicant per
   netejar-los) o escriu-los manualment amb notació `Ah Qd 5c` (rang + pal:
   `s`=espades, `h`=cors, `d`=basts, `c`=trèvols; `T`=10).
3. **Carrer**: canvia les pestanyes **Flop (3 cartes) / Turn (4) / River (5)**.
4. Prem **Analitzar** i el panell de resultats mostrarà:
   - Total de combos vàlids analitzats i combos exclosos per duplicar cartes del board.
   - Taula de freqüències + barres de progrés per categoria (jerarquia treys).
   - Desglossament de One Pair: Overpair, Top / Second / Third / Bottom Pair.
   - Desglossament de High Card: As Alt vs altres.
   - Draws: Flush Draw, OESD, Gutshot, Backdoor FD, Backdoor SD.

---

## 🔌 API (si vols integrar-la programàticament)

### `GET /`
Serveix el frontend (`frontend/index.html`).

### `GET /api/grid`
Retorna les etiquetes de la graella 13×13.

### `POST /api/analyze`
Cos de la petició (JSON):

```json
{
  "range_codes": ["AKs", "QQ"],
  "range_string": "AA+, JT",
  "board": ["Ah", "Kh", "5c"],
  "street": "flop"
}
```

- `range_codes`: llista de codis seleccionats a la graella (opcional).
- `range_string`: rang en text amb expansions `+` (opcional); es combinen ambdues.
- `board`: cartes del board en notació `Ah`, `Td`, `9c`…
- `street`: `"flop"` | `"turn"` | `"river"`.

Exemple amb curl:

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"range_string":"AKs","board":["2h","7h","Jh"],"street":"flop"}'
```

Resposta (extret):

```json
{
  "total_combos_grid": 4,
  "excluded_dupes": 0,
  "valid_combos": 4,
  "categories": [
    {"key": "FLUSH", "label": "Flush (Color)", "combos": 1, "pct": 25.0},
    {"key": "HIGH",  "label": "High Card (Carta Alta)", "combos": 3, "pct": 75.0}
  ],
  "high_card_breakdown": [
    {"key": "ACE", "label": "As Alt (Ace High)", "combos": 3, "pct": 75.0}
  ]
}
```

Documentació interactiva de l'API (generada per FastAPI): `http://127.0.0.1:8000/docs`

---

## ⚙️ Lògica clau del motor

- **Baralla disponible**: per a cada combo del rang s'exclouen les cartes presents al
  board; qualsevol combo que contingui una carta duplicada amb el board es descarta i
  es compta a `excluded_dupes` (avís visible al frontend).
- **Avaluació**: cada combo es combina amb el board i se n'avalua la millor mà de 5
  cartes amb `treys` (classificador + evaluator oficial).
- **Parelles (Top/Mid/Bottom/Overpair)**: es comparen els *rankers* de les dues cartes
  del forat amb els rankers del board. Un overpair = ambdues cartes del forat per damunt
  de totes les del board; top pair = la parella formada amb la carta més alta del board;
  second/third/bottom pair segons la posició de la carta del board emparellada.
- **Boards monocromàtics**: només es classifica com a *Flush* si el combo conté 2 cartes
  del pal del board; si en conté 1 es marca com a *Flush Draw*; si no en conté cap,
  *Backdoor FD*.
- **Expansions `+`**: `AA+` → tots els parells des d'AA fins a TT (5 parells =
  30 combos); `AKs+` → les 8 mans suited {AKs, AQs, AJs, ATs, KQs, KJs, QJs, JTs}
  expandides als seus 4 pals cadascuna (32 combos individuals). La convenció
  segueix exactament l'exemple de l'especificació del projecte.

---

## ✅ Validació interna

Escenaris de referència (comportament verificat del motor):

1. **Duplicats rang-board**: board `Ah Kh 5c` + rang `AA, AKs` → exclou Ah/Kh
   (AA→3 combos, AKs→2 combos) i mostra l'avís.
2. **Board monocromàtic**: rang `AKs` + board `2h 7h Jh` → 25% Flush (AhKh),
   75% As Alt.
3. **Jerarquia de parelles**: rang `AA, KQo, 22` + board `Ks 8d 3c` → Overpair,
   Top Pair i Bottom/Low Pair correctament separats.
4. **Parsing complex**: `AA+, AKs+` → les mans {AA, KK, QQ, JJ, TT} +
   {AKs, AQs, AJs, ATs, KQs, KJs, QJs, JTs} = 62 combos individuals de cartes
   (30 + 32). *Nota: l'endpoint `/api/analyze` exigeix sempre un board complet
   per al carrer seleccionat; aquesta expansió es pot verificar amb el parser.*
5. **Progressió de carrers**: rang `JTs` + board `9c 8d 7h` → 100% Escala a flop,
   turn i river.

---

## ❗ Problemes freqüents

| Problema | Solució |
|---|---|
| `ModuleNotFoundError: No module named 'fastapi'` | No has instal·lat les dependències o no has activat el venv: `pip install -r requirements.txt` |
| `Address already in use` al port 8000 | Canvia el port a `run.py` o tanca l'altre procés |
| Error 400 "cartes duplicades al board" | Revisa la sintaxi del board (format `Ah Td 9c`, sense repetir cartes) |
| Error 400 "El carrer X requereix N cartes" | El nombre de cartes del board ha de coincidir amb el carrer seleccionat |
| El navegador no carrega la pàgina | Assegura't que el servidor és actiu i obre `http://127.0.0.1:8000` |

---

## 🧾 Llicència / Notes

Eina personal d'anàlisi. Projecte autònom, sense serveis externs ni telemetria:
tots els càlculs es fan localment amb Python + treys.

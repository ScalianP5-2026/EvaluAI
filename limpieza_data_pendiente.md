Searched for files matching `**/mentores.csv`, 1 match

Searched for files matching `**/mentors.csv`, 1 match

Searched for files matching `**/programas_formacion.csv`, 1 match

Searched for files matching `**/courses.csv`, 1 match

Read [](file:///workspaces/EvaluAI/backend/data/raw/mentores.csv#1-1), lines 1 to 10

Read [](file:///workspaces/EvaluAI/backend/data/mentors.csv)

Aquí tienes el plan de ruta para tu futura rama. Lo he estructurado claramente con los pasos exactos a ejecutar. 

En cuanto a tu duda sobre los tutores/mentores: 
- El archivo correcto y en uso es `data/raw/mentores.csv` (contiene 56 mentores reales extraídos de vuestra base de datos, con formato `id_mentor,nombre,especialidades...`).
- El archivo falso/residual es `data/mentors.csv` (contiene solo 7 mentores de prueba en inglés ("Lucia Perez", "Data Scientist")).

*(Puedes copiar el contenido que está dentro del bloque de código inferior y guardarlo como `DATA_CLEANUP_PLAN.md` en la raíz de tu proyecto)*.

```markdown
# Plan de Acción: Limpieza de Directorio `data/` y Referencias

**Rama propuesta:** `feature/limpieza-data-files`
**Objetivo:** Purificar el árbol de datos del backend, eliminando archivos obsoletos o duplicados que entorpezcan el desarrollo, y actualizar las referencias en el código a las únicas fuentes de verdad (Single Source of Truth).

---

## 1. Archivos a Eliminar (Rutas a destruir)

Los siguientes archivos son sintéticos de versiones alfa (mock data en inglés) o exportaciones redundantes en `.xlsx` de datos que el sistema ya consume en `.csv`.

Borrar usando `rm`:
- 🔴 `backend/data/courses.csv` *(Mock data en inglés. Reemplazado por el catálogo en castellano).*
- 🔴 `backend/data/mentors.csv` *(Mock data con solo 7 mentores. Falso)*.
- 🔴 `backend/data/raw/EIPIA_FO_dataset_100_personas.csv` *(Viejo dataset pre-calculado que se rechazó metodológicamente).*
- 🔴 `backend/data/raw/courses_catalog.xlsx` *(Exportación manual. El script usa el .csv).*
- 🔴 `backend/data/raw/mentors_catalog.xlsx` *(Exportación manual. El script usa el .csv).*

---

## 2. Archivos a Reubicar (Documentación)

No son bases de datos del sistema, sino contexto para el desarrollador. Se deben sacar de `/data` a una carpeta de documentación.

Mover usando `mv`:
- 🟡 `backend/data/Sofinputs.txt` → Mover a `docs/Sofinputs_metodologia.md`.
- 🟡 `backend/data/raw/Factoria F5.pdf` → Mover a `docs/Factoria_F5_Info.pdf`.

---

## 3. The Single Source of Truth (Los intocables)

Tras la purga, el directorio `data/raw/` SOLO debe contener estos 3 archivos. Son la base sobre la que se siembra (seed) Supabase. **NO se pueden borrar ni mover.**

- 🟢 `survey_raw.xlsx`: La encuesta real de 100 empleados con las 24 variables (Escala 1-7).
- 🟢 `programas_formacion.csv`: Los 19 cursos reales disponibles.
- 🟢 `mentores.csv`: La tabla real de 56 tutores con sus especialidades (Ej: "JAA, Advanced Analytics").

*(La carpetas `/data/clean` y `/data/processed` se mantienen porque son salidas del pipeline).*

---

## 4. Cambios requeridos en Código (.py e .ipynb)

Al borrar los archivos basura, algunos scripts de configuración y Notebooks fallarán si no actualizamos sus referencias a las rutas reales.

### A. Actualizar `backend/app/config.py`
En las líneas 126-127, el sistema de variables de entorno carga los CSV viejos si falla la base de datos.
**Cambiar:**
```python
courses_path: str = os.getenv("EVALUAI_COURSES_PATH", "data/courses.csv")
mentors_path: str = os.getenv("EVALUAI_MENTORS_PATH", "data/mentors.csv")
```
**Por:**
```python
courses_path: str = os.getenv("EVALUAI_COURSES_PATH", "data/raw/programas_formacion.csv")
mentors_path: str = os.getenv("EVALUAI_MENTORS_PATH", "data/raw/mentores.csv")
```

### B. Actualizar Notebooks de Machine Learning
Los modelos de experimentación seguían utilizando el CSV obsoleto de la fase inicial. Hay que re-apuntarlos al archivo validado de la tubería.
**Archivos a editar:**
1. 00_eda_dataset.ipynb (Línea 66)
2. 01_feature_engineering.ipynb (Línea 93 aprox.)

**Cambio:**  
Reemplazar cualquier mención de `data/raw/EIPIA_FO_dataset_100_personas.xls/csv` por la ruta del archivo post-limpieza de la pipeline: `data/clean/survey_clean.csv`.

---

## Check-list final del PR
- [ ] Borrados los 5 archivos `.csv`/`.xlsx` redundantes.
- [ ] Movidos PDF y TXT explicativos a la nueva carpeta `docs/`.
- [ ] Modificado config.py para que apunte a `raw/mentores.csv` y `raw/programas_formacion.csv`.
- [ ] Modificados los notebooks Jupyter de la carpeta `ml/notebooks/` para evitar `FileNotFoundError`.
- [ ] Se ejecutó silenciosamente `docker compose restart backend` y la plataforma sigue estable no hubo errores de lectura.

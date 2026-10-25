# Git para principiantes (práctico, con este proyecto)

## 1. ¿Qué es Git, intuitivamente?

Piensa en un **videojuego con puntos de guardado**. Cada vez que algo funciona,
guardas partida. Si después rompes algo, vuelves al último punto bueno. Además
ves *qué cambió* entre un punto y otro, y *por qué* (porque cada guardado lleva
un mensaje).

| Palabra | Significado intuitivo |
|---|---|
| **Repositorio (repo)** | La carpeta del proyecto + todo su historial de guardados. |
| **Commit** | Un punto de guardado: una "foto" del proyecto con un mensaje. |
| **Rama (branch)** | Una línea paralela de trabajo. Experimentas sin tocar la versión buena. |
| **`main`** | La rama principal: la versión "oficial" del proyecto. |
| **GitHub** | La nube donde vive una copia del repo (la tuya está en `celytiorja/lab-Brazo-planar`). |
| **Clone** | Descargar el repo de GitHub a tu PC por primera vez. |
| **Pull** | Traer a tu PC los commits nuevos que hay en GitHub. |
| **Push** | Subir a GitHub tus commits locales. |
| **Pull Request (PR)** | Una petición en GitHub para unir una rama con `main`, revisando los cambios. |

**Git ≠ GitHub.** Git es el programa que guarda el historial en tu PC. GitHub es una
página web que guarda una copia en la nube y facilita compartirla.

## 2. Instalación (una sola vez)

1. Descarga **Git for Windows** desde <https://git-scm.com/download/win> e instálalo
   con las opciones por defecto.
2. Abre VS Code → `Terminal → New Terminal` y dile a Git quién eres. Esto queda
   escrito en cada commit tuyo:
   ```
   git config --global user.name "Tu Nombre"
   git config --global user.email "tu-correo@ejemplo.com"
   ```
3. Comprueba que funcionó: `git --version`

## 3. Descargar el proyecto (una sola vez)

```
cd Documents
git clone https://github.com/celytiorja/lab-Brazo-planar.git
cd lab-Brazo-planar
git checkout claude/friendly-feynman-xfljpf
code .
```

- `clone` descarga todo. La primera vez se abrirá el navegador para iniciar sesión
  en GitHub (lo gestiona el *Git Credential Manager* que viene con Git for Windows).
- `checkout <rama>` te cambia a la rama donde estamos trabajando ahora.
- `code .` abre la carpeta en VS Code.

## 4. El ciclo de cada día

```
   ┌─► git pull            (1) traer lo nuevo de GitHub (p. ej. lo que subió Claude)
   │   ...trabajas...      (2) editas código, capturas datos, etc.
   │   git status          (3) ¿qué cambió?
   │   git add <archivos>  (4) eliges qué entra en el próximo commit
   │   git commit -m "..." (5) guardas partida con un mensaje
   └── git push            (6) subes tus commits a GitHub
```

**Por qué existe `git add` (el "área de preparación"):** imagina que cambiaste 5
archivos pero solo 2 tienen que ver con "calibrar servo". Con `add` eliges esos
2 y haces un commit limpio, y los otros 3 van en otro commit con su propio mensaje.
Un historial ordenado se lee como un cuaderno de laboratorio.

### Lo mismo con botones en VS Code

Icono de **Source Control** (las tres bolitas unidas, o `Ctrl+Shift+G`):
- El **+** junto a un archivo equivale a `git add`.
- Escribes el mensaje arriba y pulsas **✓ Commit**, que equivale a `git commit`.
- **Sync Changes** / las flechas ↑↓ de la barra inferior equivalen a `git pull` + `git push`.

**Consejo:** aprende primero los comandos en la terminal. Así entiendes qué hace cada
botón, y cuando algo falle sabrás leer el error.

## 5. Buenos mensajes de commit

Un buen mensaje dice **qué** cambió y, si no es obvio, **por qué**:

| ✅ Bueno | ❌ Malo |
|---|---|
| `Agrega datos estáticos 30 s de ambas IMU` | `datos` |
| `Corrige offset del servo del codo (+7°)` | `arreglos` |
| `Ventana de media móvil configurable` | `cambios varios` |

## 6. Comandos para "mirar" (no cambian nada, úsalos sin miedo)

| Comando | Qué muestra |
|---|---|
| `git status` | Qué archivos cambiaron y cuáles están preparados. **Úsalo todo el tiempo.** |
| `git log --oneline --graph` | El historial de commits, uno por línea. |
| `git diff` | Las líneas exactas que cambiaste (aún sin `add`). |
| `git diff --staged` | Lo que ya preparaste con `add`. |
| `git branch -a` | Las ramas que existen, locales y en GitHub. |
| `git show <id>` | Qué cambió en un commit concreto. |

## 7. Deshacer cosas (con calma)

| Situación | Comando |
|---|---|
| Quiero descartar los cambios de un archivo (sin commit aún) | `git restore archivo` |
| Hice `add` de algo que no quería | `git restore --staged archivo` |
| Quiero ver cómo estaba el proyecto hace 3 commits | `git checkout <id>` (y para volver: `git checkout claude/friendly-feynman-xfljpf`) |
| Un commit ya subido tenía un error | `git revert <id>`: crea un commit nuevo que lo deshace sin borrar historia |

⚠️ Evita `git reset --hard` y `git push --force` mientras aprendes: **borran trabajo**.

## 8. Reglas de oro

1. **`git pull` antes de empezar a trabajar.** Así evitas conflictos.
2. **Commits pequeños y frecuentes**, cada uno con una sola idea.
3. **Nunca subas contraseñas ni claves.**
4. El archivo `.gitignore` lista lo que Git debe ignorar (cachés, entornos virtuales).
5. Los datos crudos de la entrega (CSV) **sí se suben**: son parte de la evidencia.

## 9. Conflictos (cuando pasen, que pasarán)

Si tú y Claude cambian la **misma línea** del mismo archivo, `git pull` te avisará
de un *conflicto*. Git marca el archivo así:

```
<<<<<<< HEAD
tu versión
=======
la versión de GitHub
>>>>>>> origin/...
```

Decides qué queda, borras las marcas, guardas y haces `git add archivo` +
`git commit`. VS Code te muestra botones "Accept Current / Incoming / Both".
No hay que temerle: es Git preguntándote algo que él no puede decidir.

## 10. Para la entrega: versión identificada

La entrega pide "commit o versión identificado". Para eso se usa una **etiqueta (tag)**:

```
git tag -a entrega1 -m "Entrega 1: cinemática + caracterización IMU"
git push origin entrega1
```

Con eso el docente puede ver exactamente esa versión aunque después sigas trabajando.

## 11. Cómo trabajamos Claude y tú en este repo

- Claude trabaja en la rama **`claude/friendly-feynman-xfljpf`** y sube ahí sus commits.
- Tú haces `git pull` para recibirlos, pruebas en el hardware y subes tus datos y cambios.
- Cuando una etapa esté terminada, abrimos un **Pull Request** hacia `main` para
  dejar la versión oficial. Lo haremos juntos la primera vez.

---

### Ejercicio de práctica (hazlo hoy)

1. Clona el repo y cámbiate a la rama (sección 3).
2. Ejecuta `git log --oneline`: verás el commit que subió Claude.
3. Abre `python/parametros.py` y pon tus medidas reales de L1 y L2.
4. `git status` → `git diff` (mira la diferencia) → `git add python/parametros.py`
   → `git commit -m "Medidas reales de L1 y L2"` → `git push`.
5. Avísale a Claude. Él hará `git pull` y verá tu commit con tu nombre. 🎉

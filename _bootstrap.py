"""
_bootstrap.py — Auto-bootstrap del venv del progetto.

Importato come PRIMA riga dagli script Python (add_players.py, run_update.py,
run_stats.py, ecc.). Se le dipendenze del progetto non sono importabili
(es. perché stai usando il Python di sistema invece del venv), questo modulo
ri-lancia automaticamente lo script con il venv del progetto.

In pratica: puoi sempre lanciare gli script con `python3 script.py` senza
preoccuparti di attivare il venv prima.
"""
import os
import sys


def _ensure_venv() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(here, "venv")
    venv_py = os.path.join(venv_dir, "bin", "python3")

    # Verifica se siamo già "dentro" il venv del progetto (sys.prefix punta a venv/).
    # Il check sui path realpath non funziona perché venv/bin/python3 è un symlink
    # al Python di sistema, ma il venv vero si distingue per sys.prefix.
    inside_venv = os.path.abspath(sys.prefix) == os.path.abspath(venv_dir)

    if not inside_venv and os.path.exists(venv_py):
        # Ri-esegui questo script con il Python del venv del progetto
        os.execv(venv_py, [venv_py] + sys.argv)
        return  # unreachable

    # Siamo nel venv (o tentativo fallito): verifica deps
    try:
        import bs4  # noqa: F401
        return  # tutto ok
    except ImportError:
        pass

    sys.stderr.write(
        "\n[ERROR] Le dipendenze del progetto non sono installate "
        "(bs4 manca dal Python in uso).\n"
        f"  Python attivo: {sys.executable}\n"
        f"  sys.prefix:    {sys.prefix}\n"
        f"  Venv atteso:   {venv_py} (esiste? {os.path.exists(venv_py)})\n\n"
        "Soluzione: lancia prima `bash start_all.sh` per creare il venv\n"
        "e installare le dipendenze, poi rilancia lo script.\n\n"
    )
    sys.exit(1)


_ensure_venv()

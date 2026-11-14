import datetime as dt
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import caminho  # noqa: E402


def test_agua_defesa_civil_2l_por_pessoa_dia():
    q = caminho.quantidades(1, 3)
    assert q["agua_l"] == 6  # Defesa Civil: 6 L em 3 dias por pessoa


def test_quantidades_familia_14_dias():
    q = caminho.quantidades(4, 14)
    assert q["agua_l"] == 112
    assert q["garrafoes_5l"] == 23          # arredonda para cima
    assert q["kcal"] == 112000
    assert q["kg_seco"] == 32.0


@pytest.mark.parametrize("p,d", [(0, 3), (2, 0), (-1, 3)])
def test_quantidades_invalidas(p, d):
    with pytest.raises(ValueError):
        caminho.quantidades(p, d)


def test_parse_riscos_limpa_e_valida():
    assert caminho.parse_riscos(" Enchente, apagao;enchente ") == ["enchente", "apagao"]
    assert caminho.parse_riscos("") == []
    with pytest.raises(ValueError):
        caminho.parse_riscos("meteoro")


def test_plano_tem_72h_14d_e_revisao_em_6_meses():
    txt = caminho.montar_plano("Silva", 2, hoje=dt.date(2026, 11, 13))
    assert "# Plano do caminho seguro — Silva" in txt
    assert "| 12 L" in txt and "| 56 L" in txt
    assert "Revisar em 14/05/2027" in txt
    for t, _ in caminho.PASSOS:
        assert t in txt
    assert "199" in txt and "193" in txt and "192" in txt


def test_plano_itens_condicionais():
    sem = caminho.montar_plano("", 1)
    assert "Fralda" not in sem and "Ração" not in sem and "Óculos" not in sem
    com = caminho.montar_plano("", 3, criancas=1, idosos=1, pets=2, remedios=True)
    assert "Fralda" in com and "Óculos" in com and "Ração" in com and "uso contínuo para 14 dias" in com


def test_plano_checklists_dos_riscos():
    txt = caminho.montar_plano("", 2, riscos=["enchente", "digital"])
    assert caminho.RISCOS["enchente"] in txt and caminho.RISCOS["digital"] in txt
    assert caminho.RISCOS["vendaval"] not in txt
    assert "40199" in txt and "APLICATIVO" in txt


def test_numero_brasileiro_na_tabela():
    txt = caminho.montar_plano("", 4)
    assert "~24.000 kcal" in txt and "≈ 6,9 kg" in txt


def test_todo_risco_tem_checklist_e_passos_existem():
    assert set(caminho.RISCOS) == set(caminho.CHECK_RISCO)
    for _, arq in caminho.PASSOS:
        assert (RAIZ / arq).is_file(), arq


def test_link_certificado_e_inema_club():
    txt = caminho.montar_plano("", 1)
    assert "nivel-ia/guia/#certificado" in txt and "https://inema.club" in txt


def test_cli_grava_arquivo(tmp_path):
    saida = tmp_path / "p.md"
    r = subprocess.run([sys.executable, str(RAIZ / "caminho.py"), "--pessoas", "3", "--riscos", "calor",
                        "--saida", str(saida)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout.startswith("ok:") and "18 L" in r.stdout
    assert caminho.RISCOS["calor"] in saida.read_text(encoding="utf-8")


def test_cli_risco_errado_sai_2(tmp_path):
    r = subprocess.run([sys.executable, str(RAIZ / "caminho.py"), "--pessoas", "1", "--riscos", "zumbi",
                        "--saida", str(tmp_path / "x.md")], capture_output=True, text=True)
    assert r.returncode == 2 and "risco desconhecido" in r.stderr


def test_cli_listar_riscos():
    r = subprocess.run([sys.executable, str(RAIZ / "caminho.py"), "--listar-riscos"], capture_output=True, text=True)
    assert r.returncode == 0 and all(k in r.stdout for k in caminho.RISCOS)


def test_sem_internet_no_codigo():
    src = (RAIZ / "caminho.py").read_text(encoding="utf-8")
    for proibido in ("import urllib", "import requests", "import socket", "http.client"):
        assert proibido not in src

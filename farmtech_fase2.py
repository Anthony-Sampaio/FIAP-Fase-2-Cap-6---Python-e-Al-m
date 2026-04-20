# =============================================================================
#  FarmTech Solutions - Fase 2
#  Sistema de gestao de talhoes para Cana-de-acucar e Laranja
#  -----------------------------------------------------------------------------
#  Evolucoes desta fase:
#    * Uso de TUPLAS para dados imutaveis (Cap. 4)
#    * Validacao de entradas com try/except (Cap. 6)
#    * Persistencia em arquivo JSON entre sessoes
# =============================================================================

import json
import os
from math import pi
from datetime import datetime

# -----------------------------------------------------------------------------
# TUPLAS - configuracoes imutaveis das culturas
# Definidas pelo programador; o usuario nao pode alterar em tempo de execucao.
# -----------------------------------------------------------------------------
config_cana = ("Cana-de-acucar", "retangular", "base x altura")
config_laranja = ("Laranja", "circular", "pi * raio^2")

# Insumo padrao por cultura (nome do insumo, dosagem por m2, unidade)
insumo_cana = ("Vinhaca", 0.0015, "L/m2")
insumo_laranja = ("Sulfato de Zinco", 0.0008, "kg/m2")

# -----------------------------------------------------------------------------
# ESTRUTURAS MUTAVEIS - dados que mudam durante a execucao
# Sao carregadas do JSON no inicio e salvas a cada alteracao.
# -----------------------------------------------------------------------------
talhoes = []       # lista de dicionarios com os talhoes cadastrados
produtores = []    # lista de dicionarios com os produtores
configuracoes = {  # configuracoes gerais do sistema
    "limite_area_alerta_m2": 100000,
    "moeda": "BRL",
    "exportar_csv_automatico": False,
    "ultima_sessao": None,
}

# Caminho do arquivo de persistencia
ARQUIVO_JSON = "farmtech_dados.json"


# =============================================================================
# FUNCOES DE PERSISTENCIA EM JSON
# =============================================================================
def salvar_dados():
    """Salva todos os dados do sistema em arquivo JSON.

    Garante a persistencia entre sessoes escrevendo talhoes, produtores
    e configuracoes em um unico arquivo estruturado.
    """
    try:
        configuracoes["ultima_sessao"] = datetime.now().isoformat(timespec="seconds")

        dados = {
            "talhoes": talhoes,
            "produtores": produtores,
            "configuracoes": configuracoes,
        }

        with open(ARQUIVO_JSON, "w", encoding="utf-8") as arq:
            json.dump(dados, arq, ensure_ascii=False, indent=4)

        return True
    except (OSError, TypeError) as erro:
        print(f"[ERRO] Nao foi possivel salvar os dados: {erro}")
        return False


def carregar_dados():
    """Carrega os dados do arquivo JSON para as estruturas em memoria.

    Se o arquivo nao existir (primeira execucao), mantem as listas vazias
    e as configuracoes padrao. Em caso de JSON corrompido, avisa o usuario
    e preserva um backup antes de reiniciar.
    """
    global talhoes, produtores, configuracoes

    if not os.path.exists(ARQUIVO_JSON):
        print("[INFO] Nenhum arquivo de dados encontrado. Iniciando sistema vazio.")
        return False

    try:
        with open(ARQUIVO_JSON, "r", encoding="utf-8") as arq:
            dados = json.load(arq)

        talhoes[:] = dados.get("talhoes", [])
        produtores[:] = dados.get("produtores", [])

        cfg_salva = dados.get("configuracoes", {})
        configuracoes.update(cfg_salva)

        ultima = configuracoes.get("ultima_sessao") or "primeira execucao"
        print(f"[OK] Dados carregados com sucesso (ultima sessao: {ultima}).")
        return True

    except json.JSONDecodeError:
        backup = ARQUIVO_JSON + ".bak"
        os.rename(ARQUIVO_JSON, backup)
        print(f"[ERRO] JSON corrompido. Backup salvo em '{backup}'. Iniciando vazio.")
        return False
    except OSError as erro:
        print(f"[ERRO] Falha ao abrir o arquivo de dados: {erro}")
        return False


def resetar_dados():
    """Apaga o arquivo JSON e zera as estruturas em memoria."""
    try:
        if os.path.exists(ARQUIVO_JSON):
            os.remove(ARQUIVO_JSON)
        talhoes.clear()
        produtores.clear()
        configuracoes.update({
            "limite_area_alerta_m2": 100000,
            "moeda": "BRL",
            "exportar_csv_automatico": False,
            "ultima_sessao": None,
        })
        print("[OK] Dados zerados com sucesso.")
    except OSError as erro:
        print(f"[ERRO] Nao foi possivel resetar os dados: {erro}")


# =============================================================================
# FUNCOES DE ENTRADA COM VALIDACAO (try/except - Cap. 6)
# =============================================================================
def ler_float(mensagem, minimo=0.0):
    """Le um numero decimal do teclado, repetindo ate ser valido."""
    while True:
        try:
            valor = float(input(mensagem).replace(",", "."))
            if valor < minimo:
                print(f"   >> Valor deve ser maior ou igual a {minimo}.")
                continue
            return valor
        except ValueError:
            print("   >> Entrada invalida. Digite um numero.")


def ler_int(mensagem, minimo=0, maximo=None):
    """Le um numero inteiro do teclado, repetindo ate ser valido."""
    while True:
        try:
            valor = int(input(mensagem))
            if valor < minimo or (maximo is not None and valor > maximo):
                limite = f" ({minimo} a {maximo})" if maximo is not None else f" (>= {minimo})"
                print(f"   >> Valor fora do intervalo permitido{limite}.")
                continue
            return valor
        except ValueError:
            print("   >> Entrada invalida. Digite um numero inteiro.")


def ler_texto(mensagem):
    """Le um texto nao vazio."""
    while True:
        texto = input(mensagem).strip()
        if texto:
            return texto
        print("   >> O campo nao pode ficar em branco.")


# =============================================================================
# CALCULOS DE AREA E INSUMOS
# =============================================================================
def calcular_area(cultura, dim1, dim2=None):
    """Calcula a area do talhao conforme a cultura.

    Cana -> retangular (base * altura)
    Laranja -> circular (pi * raio^2)
    """
    if cultura == config_cana[0]:
        return dim1 * dim2
    if cultura == config_laranja[0]:
        return pi * (dim1 ** 2)
    return 0.0


def calcular_insumo(cultura, area):
    """Retorna (nome_insumo, quantidade, unidade) para a area informada."""
    if cultura == config_cana[0]:
        return insumo_cana[0], area * insumo_cana[1], insumo_cana[2]
    if cultura == config_laranja[0]:
        return insumo_laranja[0], area * insumo_laranja[1], insumo_laranja[2]
    return "N/A", 0.0, ""


# =============================================================================
# CRUD DE TALHOES
# =============================================================================
def cadastrar_talhao():
    print("\n--- Cadastro de Talhao ---")
    print("1 - Cana-de-acucar (retangular)")
    print("2 - Laranja (circular)")
    opcao = ler_int("Escolha a cultura: ", 1, 2)

    if opcao == 1:
        cultura = config_cana[0]
        base = ler_float("Base (m): ", 0.01)
        altura = ler_float("Altura (m): ", 0.01)
        area = calcular_area(cultura, base, altura)
        dimensoes = {"base": base, "altura": altura}
    else:
        cultura = config_laranja[0]
        raio = ler_float("Raio (m): ", 0.01)
        area = calcular_area(cultura, raio)
        dimensoes = {"raio": raio}

    nome_produtor = ler_texto("Nome do produtor responsavel: ")

    insumo_nome, qtd, unidade = calcular_insumo(cultura, area)

    talhao = {
        "id": len(talhoes) + 1,
        "cultura": cultura,
        "dimensoes": dimensoes,
        "area_m2": round(area, 2),
        "produtor": nome_produtor,
        "insumo": {"nome": insumo_nome, "quantidade": round(qtd, 3), "unidade": unidade},
        "cadastrado_em": datetime.now().isoformat(timespec="seconds"),
    }
    talhoes.append(talhao)

    if area > configuracoes["limite_area_alerta_m2"]:
        print(f"   !! ALERTA: area acima do limite ({configuracoes['limite_area_alerta_m2']} m2)")

    salvar_dados()
    print(f"[OK] Talhao #{talhao['id']} cadastrado. Area = {talhao['area_m2']} m2.")


def listar_talhoes():
    print("\n--- Talhoes cadastrados ---")
    if not talhoes:
        print("Nenhum talhao cadastrado.")
        return
    for t in talhoes:
        print(
            f"#{t['id']} | {t['cultura']} | {t['area_m2']} m2 | "
            f"Produtor: {t['produtor']} | "
            f"Insumo: {t['insumo']['quantidade']} {t['insumo']['unidade']} de {t['insumo']['nome']}"
        )


def atualizar_talhao():
    listar_talhoes()
    if not talhoes:
        return
    id_talhao = ler_int("ID do talhao a atualizar: ", 1)
    for t in talhoes:
        if t["id"] == id_talhao:
            if t["cultura"] == config_cana[0]:
                t["dimensoes"]["base"] = ler_float("Nova base (m): ", 0.01)
                t["dimensoes"]["altura"] = ler_float("Nova altura (m): ", 0.01)
                area = calcular_area(t["cultura"], t["dimensoes"]["base"], t["dimensoes"]["altura"])
            else:
                t["dimensoes"]["raio"] = ler_float("Novo raio (m): ", 0.01)
                area = calcular_area(t["cultura"], t["dimensoes"]["raio"])
            t["area_m2"] = round(area, 2)
            nome, qtd, unid = calcular_insumo(t["cultura"], area)
            t["insumo"] = {"nome": nome, "quantidade": round(qtd, 3), "unidade": unid}
            salvar_dados()
            print(f"[OK] Talhao #{id_talhao} atualizado.")
            return
    print("[ERRO] Talhao nao encontrado.")


def excluir_talhao():
    listar_talhoes()
    if not talhoes:
        return
    id_talhao = ler_int("ID do talhao a excluir: ", 1)
    for i, t in enumerate(talhoes):
        if t["id"] == id_talhao:
            talhoes.pop(i)
            salvar_dados()
            print(f"[OK] Talhao #{id_talhao} removido.")
            return
    print("[ERRO] Talhao nao encontrado.")


# =============================================================================
# CRUD DE PRODUTORES
# =============================================================================
def cadastrar_produtor():
    print("\n--- Cadastro de Produtor ---")
    nome = ler_texto("Nome: ")
    cpf = ler_texto("CPF: ")
    propriedade = ler_texto("Nome da propriedade: ")
    produtores.append({
        "id": len(produtores) + 1,
        "nome": nome,
        "cpf": cpf,
        "propriedade": propriedade,
        "cadastrado_em": datetime.now().isoformat(timespec="seconds"),
    })
    salvar_dados()
    print(f"[OK] Produtor '{nome}' cadastrado.")


def listar_produtores():
    print("\n--- Produtores cadastrados ---")
    if not produtores:
        print("Nenhum produtor cadastrado.")
        return
    for p in produtores:
        print(f"#{p['id']} | {p['nome']} | CPF: {p['cpf']} | Propriedade: {p['propriedade']}")


# =============================================================================
# CONFIGURACOES DO SISTEMA
# =============================================================================
def editar_configuracoes():
    print("\n--- Configuracoes do sistema ---")
    print(f"1 - Limite de area para alerta (atual: {configuracoes['limite_area_alerta_m2']} m2)")
    print(f"2 - Moeda (atual: {configuracoes['moeda']})")
    print(f"3 - Exportar CSV automatico (atual: {configuracoes['exportar_csv_automatico']})")
    print("0 - Voltar")

    opcao = ler_int("Opcao: ", 0, 3)
    if opcao == 1:
        configuracoes["limite_area_alerta_m2"] = ler_float("Novo limite (m2): ", 1)
    elif opcao == 2:
        configuracoes["moeda"] = ler_texto("Nova moeda (ex: BRL, USD): ").upper()
    elif opcao == 3:
        escolha = ler_texto("Ativar? (s/n): ").lower()
        configuracoes["exportar_csv_automatico"] = (escolha == "s")
    else:
        return
    salvar_dados()
    print("[OK] Configuracoes atualizadas.")


# =============================================================================
# MENU PRINCIPAL
# =============================================================================
def menu():
    opcoes = {
        1: ("Cadastrar talhao", cadastrar_talhao),
        2: ("Listar talhoes", listar_talhoes),
        3: ("Atualizar talhao", atualizar_talhao),
        4: ("Excluir talhao", excluir_talhao),
        5: ("Cadastrar produtor", cadastrar_produtor),
        6: ("Listar produtores", listar_produtores),
        7: ("Editar configuracoes", editar_configuracoes),
        8: ("Resetar dados (apaga tudo)", resetar_dados),
        0: ("Sair", None),
    }
    while True:
        print("\n========= FarmTech Solutions - Fase 2 =========")
        for k, (descricao, _) in opcoes.items():
            print(f"{k} - {descricao}")
        escolha = ler_int("Escolha uma opcao: ", 0, max(opcoes.keys()))
        if escolha == 0:
            salvar_dados()
            print("Dados salvos. Ate logo!")
            break
        opcoes[escolha][1]()


# =============================================================================
# INICIALIZACAO - carrega dados automaticamente ao iniciar
# =============================================================================
if __name__ == "__main__":
    carregar_dados()
    try:
        menu()
    except KeyboardInterrupt:
        print("\n[INFO] Execucao interrompida pelo usuario. Salvando dados...")
        salvar_dados()
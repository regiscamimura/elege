FAKE_ELECTIONS = [
    {
        "id": 2040602022,
        "ano": 2022,
        "nomeEleicao": "Eleição Geral Federal 2022",
        "tipoEleicao": "O",
        "tipoAbrangencia": "F",
        "dataEleicao": "2022-10-02",
    },
]

FAKE_POSITIONS = {
    "cargos": [
        {"codigo": 6, "nome": "Deputado Federal", "contagem": 2},
    ],
}

FAKE_CANDIDATE_LIST = {
    "candidatos": [
        {
            "id": 70001000001,
            "nomeUrna": "MARIA SILVA",
            "numero": 1301,
            "nomeCompleto": "MARIA DA SILVA FERREIRA",
            "partido": {
                "numero": 13,
                "sigla": "PT",
                "nome": "Partido dos Trabalhadores",
            },
            "nomeColigacao": "Brasil da Esperança",
            "ufCandidatura": "DF",
            "descricaoSituacao": "Deferido",
        },
        {
            "id": 70001000002,
            "nomeUrna": "JOAO SOUZA",
            "numero": 2201,
            "nomeCompleto": "JOAO PEDRO DE SOUZA",
            "partido": {"numero": 22, "sigla": "PL", "nome": "Partido Liberal"},
            "nomeColigacao": "**",
            "ufCandidatura": "DF",
            "descricaoSituacao": "Deferido",
        },
    ],
}

FAKE_CANDIDATE_DETAIL_1 = {
    "id": 70001000001,
    "nomeUrna": "MARIA SILVA",
    "numero": 1301,
    "nomeCompleto": "MARIA DA SILVA FERREIRA",
    "cpf": "12345678901",
    "dataDeNascimento": "1980-05-15",
    "descricaoSexo": "FEM.",
    "descricaoCorRaca": "PARDA",
    "grauInstrucao": "Superior completo",
    "ocupacao": "Professora",
    "partido": {"numero": 13, "sigla": "PT", "nome": "Partido dos Trabalhadores"},
    "nomeColigacao": "Brasil da Esperança",
    "ufCandidatura": "DF",
    "descricaoSituacao": "Deferido",
    "fotoUrl": "https://example.com/photo1.jpg",
    "emails": ["maria@example.com"],
    "eleicoesAnteriores": [],
}

FAKE_CANDIDATE_DETAIL_2 = {
    "id": 70001000002,
    "nomeUrna": "JOAO SOUZA",
    "numero": 2201,
    "nomeCompleto": "JOAO PEDRO DE SOUZA",
    "cpf": "98765432100",
    "dataDeNascimento": "1975-11-20",
    "descricaoSexo": "MASC.",
    "descricaoCorRaca": "BRANCA",
    "grauInstrucao": "Superior completo",
    "ocupacao": "Advogado",
    "partido": {"numero": 22, "sigla": "PL", "nome": "Partido Liberal"},
    "nomeColigacao": "**",
    "ufCandidatura": "DF",
    "descricaoSituacao": "Deferido",
    "fotoUrl": "https://example.com/photo2.jpg",
    "emails": [],
    "eleicoesAnteriores": [],
}

FAKE_VOTE_SESSION = {
    "id": "2162116-169",
    "uri": "https://dadosabertos.camara.leg.br/api/v2/votacoes/2162116-169",
    "data": "2026-04-08",
    "dataHoraRegistro": "2026-04-08T20:27:11",
    "siglaOrgao": "PLEN",
    "descricao": "Aprovado o PL 1234/2025 sobre educação infantil",
    "aprovacao": 1,
}

FAKE_VOTES = [
    {
        "tipoVoto": "Sim",
        "dataRegistroVoto": "2026-04-08T20:27:11",
        "deputado_": {
            "id": 198783,
            "nome": "MARIA DA SILVA FERREIRA",
            "siglaPartido": "PT",
            "siglaUf": "DF",
            "idLegislatura": 57,
        },
    },
    {
        "tipoVoto": "Não",
        "dataRegistroVoto": "2026-04-08T20:27:11",
        "deputado_": {
            "id": 198784,
            "nome": "JOAO PEDRO DE SOUZA",
            "siglaPartido": "PL",
            "siglaUf": "DF",
            "idLegislatura": 57,
        },
    },
]


class DummyTSEBackend:
    def __init__(self):
        self.calls = []

    def get(self, path):
        self.calls.append(path)
        if path == "/eleicao/ordinarias":
            return FAKE_ELECTIONS
        if "/cargos" in path:
            return FAKE_POSITIONS
        if "/candidatos" in path:
            return FAKE_CANDIDATE_LIST
        if "/candidato/70001000001" in path:
            return FAKE_CANDIDATE_DETAIL_1
        if "/candidato/70001000002" in path:
            return FAKE_CANDIDATE_DETAIL_2
        return {}


class DummyCamaraBackend:
    def __init__(self):
        self.calls = []

    def get(self, path, params=None):
        self.calls.append((path, params))
        if path == "/deputados":
            return {"dados": []}
        if path == "/votacoes" and params:
            return {"dados": [FAKE_VOTE_SESSION]}
        if "/votos" in path:
            return {"dados": FAKE_VOTES}
        if "/votacoes/" in path:
            return {"dados": FAKE_VOTE_SESSION}
        return {"dados": []}

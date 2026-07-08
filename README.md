# Copilot Candidature

Assistente para encontrar vagas, comparar com o perfil do usuario e gerar curriculos em PDF adaptados para cada oportunidade.

## Primeira etapa

Este MVP inicial entrega:

- Cadastro de perfil profissional em formato estruturado.
- Cadastro/análise de vaga.
- Calculo simples de compatibilidade entre perfil e vaga.
- Geracao de curriculo PDF personalizado com base nas experiencias do usuario.
- Persistencia local com SQLite para perfis, vagas e candidaturas pendentes.

Automacao de inscricoes fica para uma etapa posterior e deve ser feita com revisao humana e respeito aos termos de cada plataforma.

## Como rodar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Depois acesse:

- Painel: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

## Endpoints iniciais

- `GET /`
- `GET /health`
- `POST /match`
- `POST /cv`
- `POST /cv-import/profile-draft`
- `POST /job-search/links`
- `POST /job-import/draft`
- `POST /profiles`
- `GET /profiles`
- `POST /jobs`
- `GET /jobs`
- `GET /profiles/{profile_id}/recommendations`
- `POST /profiles/{profile_id}/discover-jobs`
- `POST /applications`
- `GET /applications`
- `PATCH /applications/{application_id}/status`

## Busca no navegador

A estrategia inicial esta documentada em `docs/BROWSER_SEARCH.md`: primeiro o sistema gera links de busca e importa vagas revisadas pelo usuario; depois evolui para navegador semi-automatico com Playwright e confirmacao humana.

## Painel web

O painel em `/` permite:

- cadastrar perfil;
- importar perfil a partir de CV PDF/TXT;
- gerar links de busca;
- procurar vagas recentes automaticamente;
- usar Google Programmable Search quando `GOOGLE_API_KEY` e `GOOGLE_SEARCH_ENGINE_ID` estiverem configurados;
- importar rascunho de vaga;
- salvar vagas;
- ver ranking por perfil;
- criar candidatura com CV PDF;
- aprovar candidatura.

## Google Search

Para buscar vagas pelo Google de forma automatizada, configure a API oficial:

```env
GOOGLE_API_KEY=sua-chave
GOOGLE_SEARCH_ENGINE_ID=seu-cx
```

Sem essas variaveis, o app continua usando fontes publicas disponiveis, como Remotive, e nao tenta fazer scraping do Google.

## Testes

```bash
pytest
```

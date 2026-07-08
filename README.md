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

- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

## Endpoints iniciais

- `GET /health`
- `POST /match`
- `POST /cv`
- `POST /job-search/links`
- `POST /profiles`
- `GET /profiles`
- `POST /jobs`
- `GET /jobs`
- `GET /profiles/{profile_id}/recommendations`
- `POST /applications`
- `GET /applications`
- `PATCH /applications/{application_id}/status`

## Busca no navegador

A estrategia inicial esta documentada em `docs/BROWSER_SEARCH.md`: primeiro o sistema gera links de busca e importa vagas revisadas pelo usuario; depois evolui para navegador semi-automatico com Playwright e confirmacao humana.

## Testes

```bash
pytest
```

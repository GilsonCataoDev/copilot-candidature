# Busca de vagas no navegador

O projeto deve evoluir em tres niveis, sem comecar por automacao agressiva.

## Nivel 1 - Busca assistida

O backend gera links de busca para plataformas como LinkedIn, Indeed e Google. O usuario abre os links, revisa as vagas e cadastra no sistema as oportunidades boas.

Endpoint:

```http
POST /job-search/links
```

Exemplo de payload:

```json
{
  "role": "Desenvolvedor Python",
  "location": "Sao Paulo",
  "remote": true,
  "internship": true,
  "skills": ["FastAPI", "SQL"]
}
```

O retorno traz uma lista de URLs prontas para abrir no navegador.

## Descoberta automatica controlada

O sistema tambem consegue buscar vagas recentes na API publica da Remotive, comparar com um perfil salvo e listar as melhores oportunidades.

Endpoint:

```http
POST /profiles/{profile_id}/discover-jobs
```

Parametros uteis:

- `limit_per_term`: quantidade maxima por termo de busca.
- `max_age_days`: idade maxima da vaga.
- `minimum_score`: match minimo para entrar na lista.
- `save_top`: quantidade de vagas melhores que devem ser salvas automaticamente no banco.

A Remotive orienta evitar chamadas frequentes demais; para este MVP, use a busca algumas vezes por dia e sempre mantenha o link de origem para a vaga.

## Nivel 2 - Importacao guiada

O usuario cola um link de vaga. O sistema tenta extrair titulo, empresa, descricao, localidade e skills provaveis. Antes de salvar, o usuario revisa.

Endpoint:

```http
POST /job-import/draft
```

Exemplo de payload:

```json
{
  "url": "https://example.com/jobs/123",
  "fallback_location": "Remoto"
}
```

O endpoint tambem aceita `html` no payload para testes, extensoes de navegador ou fluxos onde a pagina ja foi aberta pelo usuario.

## Nivel 3 - Navegador semi-automatico

Com Playwright, o sistema pode abrir paginas, preencher campos simples e preparar candidaturas. O envio final deve continuar com confirmacao humana.

Esse nivel precisa respeitar:

- Termos de uso da plataforma.
- Login e captcha sem tentar burlar protecoes.
- Limite diario configuravel.
- Registro do que foi enviado.
- Revisao do CV e da mensagem antes da candidatura.

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

O sistema busca vagas recentes em fontes automatizadas permitidas, compara com um perfil salvo e lista as melhores oportunidades.

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

### Google

Busca automatica no Google deve usar API oficial. Configure:

```env
GOOGLE_API_KEY=sua-chave
GOOGLE_SEARCH_ENGINE_ID=seu-cx
```

Com essas variaveis, o backend consulta `https://www.googleapis.com/customsearch/v1` usando `key`, `cx` e `q`. Sem credenciais, o Google fica desativado e o app nao tenta contornar captcha, login, limites ou termos de uso.

Observacao: a documentacao atual do Google informa que a Custom Search JSON API exige API key e Programmable Search Engine ID, e tambem indica que o produto esta fechado para novos clientes. Quem nao tiver acesso deve usar outra fonte/API oficial.

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

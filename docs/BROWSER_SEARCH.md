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

## Nivel 2 - Importacao guiada

O usuario cola um link de vaga. O sistema tenta extrair titulo, empresa, descricao, localidade e skills provaveis. Antes de salvar, o usuario revisa.

## Nivel 3 - Navegador semi-automatico

Com Playwright, o sistema pode abrir paginas, preencher campos simples e preparar candidaturas. O envio final deve continuar com confirmacao humana.

Esse nivel precisa respeitar:

- Termos de uso da plataforma.
- Login e captcha sem tentar burlar protecoes.
- Limite diario configuravel.
- Registro do que foi enviado.
- Revisao do CV e da mensagem antes da candidatura.


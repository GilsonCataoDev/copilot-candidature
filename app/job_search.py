from urllib.parse import quote_plus, urlencode

from app.models import JobSearchLink, JobSearchPlan, JobSearchRequest, SearchProvider


def build_query(request: JobSearchRequest) -> str:
    parts = [request.role]
    if request.internship:
        parts.append("estagio")
    if request.remote:
        parts.append("remoto")
    parts.extend(request.skills[:4])
    if request.location:
        parts.append(request.location)
    return " ".join(part for part in parts if part.strip())


def build_linkedin_url(query: str, request: JobSearchRequest) -> str:
    params = {"keywords": query}
    if request.location:
        params["location"] = request.location
    if request.remote:
        params["f_WT"] = "2"
    if request.internship:
        params["f_E"] = "1"
    return "https://www.linkedin.com/jobs/search/?" + urlencode(params)


def build_indeed_url(query: str, request: JobSearchRequest) -> str:
    params = {"q": query}
    if request.location:
        params["l"] = request.location
    if request.remote:
        params["sc"] = "0kf%3Aattr%28DSQF7%29%3B"
    return "https://br.indeed.com/jobs?" + urlencode(params)


def build_google_url(query: str) -> str:
    enriched = f'{query} ("vaga" OR "estagio") site:linkedin.com/jobs OR site:gupy.io'
    return "https://www.google.com/search?q=" + quote_plus(enriched)


def build_search_plan(request: JobSearchRequest) -> JobSearchPlan:
    query = build_query(request)
    searches = []

    if SearchProvider.linkedin in request.providers:
        searches.append(
            JobSearchLink(
                provider=SearchProvider.linkedin,
                label="Buscar no LinkedIn",
                url=build_linkedin_url(query, request),
                query=query,
            )
        )

    if SearchProvider.indeed in request.providers:
        searches.append(
            JobSearchLink(
                provider=SearchProvider.indeed,
                label="Buscar no Indeed",
                url=build_indeed_url(query, request),
                query=query,
            )
        )

    if SearchProvider.google in request.providers:
        searches.append(
            JobSearchLink(
                provider=SearchProvider.google,
                label="Buscar no Google",
                url=build_google_url(query),
                query=query,
            )
        )

    return JobSearchPlan(searches=searches)

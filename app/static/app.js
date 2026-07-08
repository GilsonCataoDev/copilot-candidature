const state = {
  profiles: [],
  jobs: [],
  applications: [],
};

const statusMessage = document.querySelector("#statusMessage");

function splitList(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function selectedValues(form, name) {
  return [...form.querySelectorAll(`input[name="${name}"]:checked`)].map((input) => input.value);
}

function setStatus(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.classList.toggle("error", isError);
}

function errorMessage(body, fallback) {
  if (typeof body.detail === "string") {
    return body.detail;
  }
  if (Array.isArray(body.detail)) {
    return body.detail.map((item) => item.msg || JSON.stringify(item)).join(" ");
  }
  if (body.detail) {
    return JSON.stringify(body.detail);
  }
  return fallback;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(errorMessage(body, `Erro HTTP ${response.status}`));
  }

  return response.json();
}

async function apiForm(path, formData) {
  const response = await fetch(path, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(errorMessage(body, `Erro HTTP ${response.status}`));
  }

  return response.json();
}

function renderProfiles() {
  const select = document.querySelector("#profileSelect");
  select.innerHTML = state.profiles
    .map((item) => `<option value="${item.id}">#${item.id} ${item.profile.full_name}</option>`)
    .join("");
}

function renderJobs() {
  const list = document.querySelector("#jobsList");
  if (!state.jobs.length) {
    list.innerHTML = '<p class="meta">Nenhuma vaga salva ainda.</p>';
    return;
  }

  list.innerHTML = state.jobs
    .map(
      (item) => `
        <div>
          <strong>#${item.id} ${item.job.title}</strong>
          <span class="meta">${item.job.company}</span>
        </div>
      `,
    )
    .join("");
}

function renderApplications() {
  const target = document.querySelector("#applications");
  if (!state.applications.length) {
    target.innerHTML = '<p class="meta">Nenhuma candidatura criada ainda.</p>';
    return;
  }

  target.innerHTML = state.applications
    .map(
      (item) => `
        <article class="card">
          <h3>Candidatura #${item.id}</h3>
          <p class="meta">Perfil #${item.profile_id} - Vaga #${item.job_id}</p>
          <p><span class="score">${item.match.score}% match</span> Status: ${item.status}</p>
          ${item.cv_path ? `<p class="meta">CV: ${item.cv_path}</p>` : ""}
          <button class="secondary" data-approve="${item.id}" type="button">Marcar como aprovada</button>
        </article>
      `,
    )
    .join("");

  target.querySelectorAll("[data-approve]").forEach((button) => {
    button.addEventListener("click", async () => {
      await api(`/applications/${button.dataset.approve}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: "approved" }),
      });
      setStatus("Candidatura atualizada.");
      await loadData();
    });
  });
}

function renderDiscoveredJobs(result) {
  const target = document.querySelector("#recommendations");
  if (!result.jobs.length) {
    target.innerHTML = '<p class="meta">Nenhuma vaga recente compativel encontrada.</p>';
    return;
  }

  target.innerHTML = result.jobs
    .map(
      (item) => `
        <article class="card">
          <h3>${item.job.title}</h3>
          <p class="meta">${item.job.company} - ${item.job.location || "Local nao informado"}</p>
          <p><span class="score">${item.match.score}% match</span> Fonte: ${item.source}</p>
          <p class="meta">Publicado: ${item.published_at || "nao informado"}</p>
          <p class="meta">${item.match.recommendation}</p>
          <a href="${item.job.url}" target="_blank" rel="noreferrer">Abrir vaga original</a>
        </article>
      `,
    )
    .join("");
}

async function runDiscovery(profileId, saveTop = 5) {
  setStatus("Procurando vagas recentes e calculando compatibilidade...");
  const result = await api(
    `/profiles/${profileId}/discover-jobs?limit_per_term=10&max_age_days=30&minimum_score=35&save_top=${saveTop}`,
    { method: "POST" },
  );
  renderDiscoveredJobs(result);
  await loadData();
  setStatus(`${result.jobs.length} vagas encontradas. ${result.imported_count} importadas.`);
}

async function loadData() {
  const [profiles, jobs, applications] = await Promise.all([
    api("/profiles"),
    api("/jobs"),
    api("/applications"),
  ]);
  state.profiles = profiles;
  state.jobs = jobs;
  state.applications = applications;
  renderProfiles();
  renderJobs();
  renderApplications();
}

document.querySelector("#profileForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const profile = {
    full_name: data.get("full_name"),
    email: data.get("email"),
    location: data.get("location") || null,
    summary: data.get("summary") || null,
    skills: splitList(data.get("skills") || ""),
    target_roles: splitList(data.get("target_roles") || ""),
    preferred_work_modes: selectedValues(form, "preferred_work_modes"),
  };

  const savedProfile = await api("/profiles", { method: "POST", body: JSON.stringify(profile) });
  form.reset();
  await loadData();
  await runDiscovery(savedProfile.id);
});

document.querySelector("#cvUploadForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const draft = await apiForm("/cv-import/profile-draft", data);

  document.querySelector("#cvDraft").innerHTML = `
    <article class="card">
      <h3>${draft.profile.full_name}</h3>
      <p class="meta">${draft.profile.email}</p>
      <p>${draft.profile.summary || ""}</p>
      <p class="meta">Skills: ${draft.extracted_skills.join(", ") || "revisar manualmente"}</p>
      <p class="meta">Cargos: ${draft.profile.target_roles.join(", ") || "revisar manualmente"}</p>
      ${
        draft.review_notes.length
          ? `<p class="meta">Revisar: ${draft.review_notes.join(" ")}</p>`
          : ""
      }
      <button id="saveCvProfile" type="button">Salvar perfil importado</button>
    </article>
  `;

  document.querySelector("#saveCvProfile").addEventListener("click", async () => {
    const savedProfile = await api("/profiles", {
      method: "POST",
      body: JSON.stringify(draft.profile),
    });
    await loadData();
    await runDiscovery(savedProfile.id);
  });
});

document.querySelector("#searchForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const plan = await api("/job-search/links", {
    method: "POST",
    body: JSON.stringify({
      role: data.get("role"),
      location: data.get("location") || null,
      remote: data.get("remote") === "on",
      internship: data.get("internship") === "on",
      skills: splitList(data.get("skills") || ""),
    }),
  });

  document.querySelector("#searchLinks").innerHTML = plan.searches
    .map(
      (search) => `
        <article class="card">
          <h3>${search.label}</h3>
          <p class="meta">${search.query}</p>
          <a href="${search.url}" target="_blank" rel="noreferrer">Abrir busca</a>
        </article>
      `,
    )
    .join("");
  setStatus("Links de busca gerados.");
});

document.querySelector("#importForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const draft = await api("/job-import/draft", {
    method: "POST",
    body: JSON.stringify({
      url: data.get("url"),
      html: data.get("html") || null,
      fallback_location: data.get("fallback_location") || null,
    }),
  });

  const target = document.querySelector("#importDraft");
  target.innerHTML = `
    <article class="card">
      <h3>${draft.job.title}</h3>
      <p class="meta">${draft.job.company} ${draft.job.location ? `- ${draft.job.location}` : ""}</p>
      <p>${draft.job.description}</p>
      <p class="meta">Skills: ${draft.extracted_skills.join(", ") || "revisar manualmente"}</p>
      ${
        draft.review_notes.length
          ? `<p class="meta">Revisar: ${draft.review_notes.join(" ")}</p>`
          : ""
      }
      <button id="saveDraftJob" type="button">Salvar vaga</button>
    </article>
  `;

  document.querySelector("#saveDraftJob").addEventListener("click", async () => {
    await api("/jobs", { method: "POST", body: JSON.stringify(draft.job) });
    setStatus("Vaga salva.");
    await loadData();
  });
});

document.querySelector("#recommendButton").addEventListener("click", async () => {
  const profileId = document.querySelector("#profileSelect").value;
  if (!profileId) {
    setStatus("Salve um perfil antes de gerar recomendacoes.", true);
    return;
  }

  const recommendations = await api(`/profiles/${profileId}/recommendations?minimum_score=0`);
  const target = document.querySelector("#recommendations");
  if (!recommendations.length) {
    target.innerHTML = '<p class="meta">Nenhuma vaga encontrada para esse perfil.</p>';
    return;
  }

  target.innerHTML = recommendations
    .map(
      (item) => `
        <article class="card">
          <h3>${item.job.title}</h3>
          <p class="meta">${item.job.company}</p>
          <p><span class="score">${item.match.score}% match</span></p>
          <p class="meta">${item.match.recommendation}</p>
          <button data-apply="${item.job_id}" type="button">Criar candidatura</button>
        </article>
      `,
    )
    .join("");

  target.querySelectorAll("[data-apply]").forEach((button) => {
    button.addEventListener("click", async () => {
      await api("/applications", {
        method: "POST",
        body: JSON.stringify({
          profile_id: Number(profileId),
          job_id: Number(button.dataset.apply),
          generate_cv: true,
        }),
      });
      setStatus("Candidatura criada com CV gerado.");
      await loadData();
    });
  });
});

document.querySelector("#discoverButton").addEventListener("click", async () => {
  const profileId = document.querySelector("#profileSelect").value;
  if (!profileId) {
    setStatus("Salve um perfil antes de procurar vagas recentes.", true);
    return;
  }

  const saveTop = Number(document.querySelector("#saveTopInput").value || 0);
  setStatus("Procurando vagas recentes nas fontes disponiveis...");
  const result = await api(
    `/profiles/${profileId}/discover-jobs?limit_per_term=10&max_age_days=14&minimum_score=40&save_top=${saveTop}`,
    { method: "POST" },
  );

  const target = document.querySelector("#recommendations");
  if (!result.jobs.length) {
    target.innerHTML = '<p class="meta">Nenhuma vaga recente compativel encontrada.</p>';
    setStatus("Busca concluida sem vagas compatíveis.");
    return;
  }

  target.innerHTML = result.jobs
    .map(
      (item) => `
        <article class="card">
          <h3>${item.job.title}</h3>
          <p class="meta">${item.job.company} - ${item.job.location || "Remote"}</p>
          <p><span class="score">${item.match.score}% match</span> Fonte: ${item.source}</p>
          <p class="meta">Publicado: ${item.published_at || "nao informado"}</p>
          <a href="${item.job.url}" target="_blank" rel="noreferrer">Abrir vaga original</a>
        </article>
      `,
    )
    .join("");

  setStatus(`${result.jobs.length} vagas encontradas. ${result.imported_count} importadas.`);
  await loadData();
});

document.querySelector("#refreshButton").addEventListener("click", async () => {
  await loadData();
  setStatus("Dados atualizados.");
});

loadData().catch((error) => setStatus(error.message, true));

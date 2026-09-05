import { useEffect, useState } from "react";
import {
  ApiError,
  addCandidate,
  bulkAddCandidates,
  closeElection,
  createElection,
  listCandidates,
  openElection,
} from "../api";
import PrivateKeyReveal from "./PrivateKeyReveal";

const STATUS_LABEL = {
  DRAFT: "Nije otvoren",
  OPEN: "Otvoren",
  CLOSED: "Zatvoren",
};

// datetime-local input prima/vraca lokalno vrijeme bez vremenske zone
// (npr. "2026-09-07T07:00") - pretvorba u UTC ISO ide preko new Date(...)
// koji ga tumaci kao LOKALNO vrijeme preglednika, sto je upravo ono sto
// admin ocekuje ("otvori u nedjelju u 7 ujutro" = 7 ujutro po njegovom
// vremenu, ne po UTC-u).
function toIsoOrNull(localDatetimeValue) {
  if (!localDatetimeValue) return null;
  return new Date(localDatetimeValue).toISOString();
}

function formatDateTime(isoValue) {
  if (!isoValue) return null;
  return new Date(isoValue).toLocaleString("hr-HR", { dateStyle: "medium", timeStyle: "short" });
}

// Vrijednost za min= atribut datetime-local inputa - trenutno lokalno
// vrijeme, da admin ne moze slucajno zakazati otvaranje/zatvaranje u proslosti.
function nowLocalInputValue() {
  const d = new Date();
  d.setSeconds(0, 0);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function CandidateManager({ token, election, onElectionsChanged }) {
  const [candidates, setCandidates] = useState([]);
  const [loadingCandidates, setLoadingCandidates] = useState(true);
  const [newName, setNewName] = useState("");
  const [bulkText, setBulkText] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [openResult, setOpenResult] = useState(null); // { private_key_pem }
  const [openNotice, setOpenNotice] = useState("");

  const reloadCandidates = () => {
    setLoadingCandidates(true);
    listCandidates(token, election.id)
      .then(setCandidates)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Greška pri učitavanju kandidata."))
      .finally(() => setLoadingCandidates(false));
  };

  useEffect(() => {
    reloadCandidates();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [election.id]);

  const handleAddOne = async (event) => {
    event.preventDefault();
    if (!newName.trim()) return;
    setBusy(true);
    setError("");
    try {
      await addCandidate(token, election.id, newName.trim());
      setNewName("");
      reloadCandidates();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Greška pri dodavanju kandidata.");
    } finally {
      setBusy(false);
    }
  };

  const handleAddBulk = async (event) => {
    event.preventDefault();
    const names = bulkText
      .split("\n")
      .map((n) => n.trim())
      .filter(Boolean);
    if (names.length === 0) return;
    setBusy(true);
    setError("");
    try {
      await bulkAddCandidates(token, election.id, names);
      setBulkText("");
      reloadCandidates();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Greška pri dodavanju kandidata.");
    } finally {
      setBusy(false);
    }
  };

  const handleOpen = async () => {
    if (candidates.length === 0) {
      setError("Izbor mora imati barem jednog kandidata prije otvaranja.");
      return;
    }
    const confirmMsg = election.scheduled_open_at
      ? `Izbor "${election.name}" je zakazan za ${formatDateTime(election.scheduled_open_at)}. Otvoriti ga ranije, odmah? Nakon ovoga kandidati se više ne mogu mijenjati.`
      : `Otvoriti izbor "${election.name}"? Nakon ovoga kandidati se više ne mogu mijenjati.`;
    if (!window.confirm(confirmMsg)) {
      return;
    }
    setBusy(true);
    setError("");
    setOpenNotice("");
    try {
      const data = await openElection(token, election.id);
      onElectionsChanged();
      if (data.private_key_pem) {
        // Nema zakazivanja (ili je zakazivanje nekako promasilo) - kljuc se
        // generira upravo sada, prvi i jedini put, pa ga treba pokazati.
        setOpenResult(data);
      } else {
        // Izbor je bio zakazan - kljuc je vec pokazan administratoru kod
        // kreiranja izbora (vidi ElectionsTab.handleCreate), pa se ovdje
        // NE generira/prikazuje novi (RULE 34.1 - kljuc se pokazuje samo
        // jednom).
        setOpenNotice("Izbor je otvoren. Privatni ključ je već bio prikazan prilikom zakazivanja izbora.");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Greška pri otvaranju izbora.");
    } finally {
      setBusy(false);
    }
  };

  const handleClose = async () => {
    if (!window.confirm(`Zatvoriti izbor "${election.name}"? Nakon ovoga glasanje više nije moguće.`)) {
      return;
    }
    setBusy(true);
    setError("");
    try {
      await closeElection(token, election.id);
      onElectionsChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Greška pri zatvaranju izbora.");
    } finally {
      setBusy(false);
    }
  };

  if (openResult) {
    return (
      <PrivateKeyReveal
        privateKeyPem={openResult.private_key_pem}
        heading="Izbor je otvoren."
        onAcknowledge={() => setOpenResult(null)}
      />
    );
  }

  return (
    <div>
      {error && <div className="alert alert-danger py-2">{error}</div>}
      {openNotice && (
        <div className="alert alert-success py-2 d-flex justify-content-between align-items-center">
          <span>{openNotice}</span>
          <button
            type="button"
            className="btn-close"
            aria-label="Zatvori"
            onClick={() => setOpenNotice("")}
          />
        </div>
      )}
      {(election.scheduled_open_at || election.scheduled_close_at) && (
        <p className="text-muted small mb-3">
          ⏰ Zakazano otvaranje: {formatDateTime(election.scheduled_open_at) || "-"} · Zakazano zatvaranje:{" "}
          {formatDateTime(election.scheduled_close_at) || "-"}
        </p>
      )}

      {loadingCandidates ? (
        <p className="text-muted">Učitavam kandidate...</p>
      ) : (
        <table className="table vote-count-table mb-3">
          <thead>
            <tr>
              <th>#</th>
              <th>Kandidat</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((c) => (
              <tr key={c.id}>
                <td>{c.display_order}</td>
                <td>{c.name}</td>
              </tr>
            ))}
            {candidates.length === 0 && (
              <tr>
                <td colSpan={2} className="text-muted">
                  Nema još dodanih kandidata.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      {election.status === "DRAFT" && (
        <>
          <form onSubmit={handleAddOne} className="d-flex gap-2 mb-3">
            <input
              className="form-control"
              placeholder="Ime i prezime kandidata"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              disabled={busy}
            />
            <button type="submit" className="btn admin-btn text-white" disabled={busy || !newName.trim()}>
              Dodaj
            </button>
          </form>

          <form onSubmit={handleAddBulk} className="mb-3">
            <label className="form-label small text-muted">Dodaj više odjednom (jedno ime po retku)</label>
            <textarea
              className="form-control mb-2"
              rows={3}
              placeholder={"Ana Anić\nIvan Ivić\nMarko Marić"}
              value={bulkText}
              onChange={(e) => setBulkText(e.target.value)}
              disabled={busy}
            />
            <button type="submit" className="btn btn-outline-secondary btn-sm" disabled={busy || !bulkText.trim()}>
              Dodaj sve odjednom
            </button>
          </form>

          <button type="button" className="btn admin-btn text-white" onClick={handleOpen} disabled={busy}>
            Otvori izbor
          </button>
        </>
      )}

      {election.status === "OPEN" && (
        <button type="button" className="btn btn-outline-danger" onClick={handleClose} disabled={busy}>
          Zatvori izbor
        </button>
      )}

      {election.status === "CLOSED" && (
        <p className="text-muted small mb-0">
          Izbor je zatvoren. Brojanje glasova (Tally) dostupno je na kartici "Nadzor".
        </p>
      )}
    </div>
  );
}

export default function ElectionsTab({ token, elections, onElectionsChanged }) {
  const [newElectionName, setNewElectionName] = useState("");
  const [scheduledOpenAt, setScheduledOpenAt] = useState("");
  const [scheduledCloseAt, setScheduledCloseAt] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [expandedId, setExpandedId] = useState(null);
  // Kljuc dobiven ODMAH pri kreiranju izbora sa zakazanim otvaranjem (vidi
  // PrivateKeyReveal) - drzi se ovdje, na razini cijelog taba, jer u trenutku
  // kreiranja jos ne postoji rasklopljeni red za taj izbor.
  const [createdKeyInfo, setCreatedKeyInfo] = useState(null); // { electionName, electionId, private_key_pem }

  const handleCreate = async (event) => {
    event.preventDefault();
    if (!newElectionName.trim()) return;
    if (scheduledOpenAt && scheduledCloseAt && new Date(scheduledCloseAt) <= new Date(scheduledOpenAt)) {
      setCreateError("Zakazano zatvaranje mora biti nakon zakazanog otvaranja.");
      return;
    }
    setCreating(true);
    setCreateError("");
    try {
      const election = await createElection(
        token,
        newElectionName.trim(),
        toIsoOrNull(scheduledOpenAt),
        toIsoOrNull(scheduledCloseAt),
      );
      setNewElectionName("");
      setScheduledOpenAt("");
      setScheduledCloseAt("");
      onElectionsChanged();
      if (election.private_key_pem) {
        setCreatedKeyInfo({
          electionName: election.name,
          electionId: election.id,
          private_key_pem: election.private_key_pem,
        });
      } else {
        setExpandedId(election.id);
      }
    } catch (err) {
      setCreateError(err instanceof ApiError ? err.message : "Greška pri kreiranju izbora.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div>
      <div className="admin-card">
        <h2 className="h5 mb-3">Novi izbor</h2>
        <form onSubmit={handleCreate}>
          <div className="d-flex gap-2 mb-3">
            <input
              className="form-control"
              placeholder="Naziv izbora (npr. Predsjednički izbori 2026.)"
              value={newElectionName}
              onChange={(e) => setNewElectionName(e.target.value)}
              disabled={creating}
            />
            <button
              type="submit"
              className="btn admin-btn text-white text-nowrap"
              disabled={creating || !newElectionName.trim()}
            >
              Kreiraj izbor
            </button>
          </div>
          <p className="text-muted small mb-2">
            Zakazivanje je opcionalno - ako se ostavi prazno, izbor se otvara i zatvara ručno klikom na
            gumb ("Otvori izbor" / "Zatvori izbor") kao i do sad.
          </p>
          <div className="row g-2">
            <div className="col-sm-6">
              <label className="form-label small text-muted" htmlFor="scheduledOpenAt">
                Zakazano otvaranje (opcionalno)
              </label>
              <input
                id="scheduledOpenAt"
                type="datetime-local"
                className="form-control"
                value={scheduledOpenAt}
                min={nowLocalInputValue()}
                onChange={(e) => setScheduledOpenAt(e.target.value)}
                disabled={creating}
              />
            </div>
            <div className="col-sm-6">
              <label className="form-label small text-muted" htmlFor="scheduledCloseAt">
                Zakazano zatvaranje (opcionalno)
              </label>
              <input
                id="scheduledCloseAt"
                type="datetime-local"
                className="form-control"
                value={scheduledCloseAt}
                min={scheduledOpenAt || nowLocalInputValue()}
                onChange={(e) => setScheduledCloseAt(e.target.value)}
                disabled={creating}
              />
            </div>
          </div>
        </form>
        {createError && <div className="alert alert-danger py-2 mt-2 mb-0">{createError}</div>}
      </div>

      {createdKeyInfo && (
        <div className="admin-card">
          <PrivateKeyReveal
            privateKeyPem={createdKeyInfo.private_key_pem}
            heading={`Izbor "${createdKeyInfo.electionName}" je zakazan.`}
            onAcknowledge={() => {
              setExpandedId(createdKeyInfo.electionId);
              setCreatedKeyInfo(null);
            }}
          />
        </div>
      )}

      <div className="admin-card">
        <h2 className="h5 mb-3">Svi izbori</h2>
        {elections.length === 0 && <p className="text-muted mb-0">Još nema kreiranih izbora.</p>}
        {elections.map((election) => (
          <div key={election.id} className="election-row">
            <button
              type="button"
              className="election-row-header"
              onClick={() => setExpandedId(expandedId === election.id ? null : election.id)}
            >
              <span className="fw-semibold">{election.name}</span>
              <span className="d-flex align-items-center gap-2">
                {(election.scheduled_open_at || election.scheduled_close_at) && (
                  <span className="text-muted small" title="Zakazano otvaranje / zatvaranje">
                    ⏰ {formatDateTime(election.scheduled_open_at) || "-"}
                    {" → "}
                    {formatDateTime(election.scheduled_close_at) || "-"}
                  </span>
                )}
                <span className={`status-badge status-${election.status.toLowerCase()}`}>
                  {STATUS_LABEL[election.status] || election.status}
                </span>
              </span>
            </button>
            {expandedId === election.id && (
              <div className="election-row-body">
                <CandidateManager token={token} election={election} onElectionsChanged={onElectionsChanged} />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

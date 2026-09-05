import { useEffect, useMemo, useState } from "react";
import { ApiError, bulkCreateStations, createStation, listStations } from "../api";

// Ista lista zupanija kao u backend app/elections/regions.py - koristi se
// samo kao prijedlog (datalist) da se admin ne prekuca, ne validira se
// strogo na frontendu (bulk import prihvaca i nepoznate vrijednosti).
const KNOWN_ZUPANIJE = [
  "Zagrebačka županija",
  "Krapinsko-zagorska županija",
  "Varaždinska županija",
  "Koprivničko-križevačka županija",
  "Međimurska županija",
  "Sisačko-moslavačka županija",
  "Karlovačka županija",
  "Bjelovarsko-bilogorska županija",
  "Virovitičko-podravska županija",
  "Požeško-slavonska županija",
  "Brodsko-posavska županija",
  "Osječko-baranjska županija",
  "Vukovarsko-srijemska županija",
  "Primorsko-goranska županija",
  "Ličko-senjska županija",
  "Zadarska županija",
  "Šibensko-kninska županija",
  "Splitsko-dalmatinska županija",
  "Istarska županija",
  "Dubrovačko-neretvanska županija",
  "Grad Zagreb",
  "Dijaspora",
];

function parseBulkText(text) {
  // format po retku: sifra,naziv,zupanija,broj_biraca (zupanija i broj_biraca opcionalni)
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const parts = line.split(",").map((p) => p.trim());
      const [code, name, zupanija, registeredVoters] = parts;
      return {
        code,
        name: name || code,
        zupanija: zupanija || null,
        registered_voters: registeredVoters ? parseInt(registeredVoters, 10) || 300 : 300,
      };
    })
    .filter((s) => s.code);
}

export default function StationsTab({ token }) {
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [regionFilter, setRegionFilter] = useState("");

  const [form, setForm] = useState({ code: "", name: "", zupanija: "", registered_voters: 300 });
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");

  const [bulkText, setBulkText] = useState("");
  const [bulkBusy, setBulkBusy] = useState(false);
  const [bulkResult, setBulkResult] = useState(null);
  const [bulkError, setBulkError] = useState("");

  const reload = () => {
    setLoading(true);
    listStations(token)
      .then(setStations)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Greška pri učitavanju biračkih mjesta."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const regions = useMemo(() => {
    const set = new Set(stations.map((s) => s.region).filter(Boolean));
    return Array.from(set).sort();
  }, [stations]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return stations.filter((s) => {
      if (regionFilter && s.region !== regionFilter) return false;
      if (!q) return true;
      return s.code.toLowerCase().includes(q) || s.name.toLowerCase().includes(q) || (s.zupanija || "").toLowerCase().includes(q);
    });
  }, [stations, search, regionFilter]);

  const handleCreate = async (event) => {
    event.preventDefault();
    setCreating(true);
    setCreateError("");
    try {
      await createStation(token, {
        code: form.code.trim(),
        name: form.name.trim(),
        zupanija: form.zupanija.trim() || null,
        registered_voters: Number(form.registered_voters) || 300,
      });
      setForm({ code: "", name: "", zupanija: "", registered_voters: 300 });
      reload();
    } catch (err) {
      setCreateError(err instanceof ApiError ? err.message : "Greška pri kreiranju biračkog mjesta.");
    } finally {
      setCreating(false);
    }
  };

  const handleBulkImport = async (event) => {
    event.preventDefault();
    const rows = parseBulkText(bulkText);
    if (rows.length === 0) return;
    setBulkBusy(true);
    setBulkError("");
    setBulkResult(null);
    try {
      const result = await bulkCreateStations(token, rows);
      setBulkResult(result);
      setBulkText("");
      reload();
    } catch (err) {
      setBulkError(err instanceof ApiError ? err.message : "Greška pri uvozu biračkih mjesta.");
    } finally {
      setBulkBusy(false);
    }
  };

  return (
    <div>
      <div className="admin-card">
        <h2 className="h5 mb-3">Novo biračko mjesto</h2>
        <form onSubmit={handleCreate} className="row g-2 align-items-end">
          <div className="col-md-2">
            <label className="form-label small">Šifra</label>
            <input
              className="form-control"
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })}
              disabled={creating}
              required
            />
          </div>
          <div className="col-md-3">
            <label className="form-label small">Naziv</label>
            <input
              className="form-control"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              disabled={creating}
              required
            />
          </div>
          <div className="col-md-3">
            <label className="form-label small">Županija</label>
            <input
              className="form-control"
              list="zupanije-datalist"
              value={form.zupanija}
              onChange={(e) => setForm({ ...form, zupanija: e.target.value })}
              disabled={creating}
            />
            <datalist id="zupanije-datalist">
              {KNOWN_ZUPANIJE.map((z) => (
                <option key={z} value={z} />
              ))}
            </datalist>
          </div>
          <div className="col-md-2">
            <label className="form-label small">Broj birača</label>
            <input
              type="number"
              min={1}
              className="form-control"
              value={form.registered_voters}
              onChange={(e) => setForm({ ...form, registered_voters: e.target.value })}
              disabled={creating}
            />
          </div>
          <div className="col-md-2">
            <button type="submit" className="btn admin-btn text-white w-100" disabled={creating}>
              Dodaj
            </button>
          </div>
        </form>
        {createError && <div className="alert alert-danger py-2 mt-2 mb-0">{createError}</div>}
      </div>

      <div className="admin-card">
        <h2 className="h5 mb-2">Skupni uvoz (bulk import)</h2>
        <p className="text-muted small mb-2">
          Jedan redak po biralištu, odvojeno zarezima: <code>šifra,naziv,županija,broj_birača</code> (županija i
          broj birača su opcionalni).
        </p>
        <form onSubmit={handleBulkImport}>
          <textarea
            className="form-control mb-2"
            rows={4}
            placeholder={"NOVO-MJESTO,Novo biralište,Zagrebačka županija,250\nDRUGO-MJESTO,Drugo biralište"}
            value={bulkText}
            onChange={(e) => setBulkText(e.target.value)}
            disabled={bulkBusy}
          />
          <button type="submit" className="btn btn-outline-secondary btn-sm" disabled={bulkBusy || !bulkText.trim()}>
            Uvezi sva biračka mjesta
          </button>
        </form>
        {bulkError && <div className="alert alert-danger py-2 mt-2 mb-0">{bulkError}</div>}
        {bulkResult && (
          <div className="alert alert-success py-2 mt-2 mb-0">
            Uvezeno {bulkResult.created.length} novih biračkih mjesta.
            {bulkResult.skipped_codes.length > 0 && (
              <> Preskočeno (šifra već postoji): {bulkResult.skipped_codes.join(", ")}.</>
            )}
          </div>
        )}
      </div>

      <div className="admin-card">
        <div className="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
          <h2 className="h5 mb-0">
            Sva biračka mjesta <span className="text-muted fw-normal">({filtered.length} / {stations.length})</span>
          </h2>
          <div className="d-flex gap-2">
            <input
              className="form-control form-control-sm"
              style={{ width: "220px" }}
              placeholder="Pretraži šifru/naziv/županiju..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select
              className="form-select form-select-sm"
              style={{ width: "200px" }}
              value={regionFilter}
              onChange={(e) => setRegionFilter(e.target.value)}
            >
              <option value="">Sve regije</option>
              {regions.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && <div className="alert alert-danger py-2">{error}</div>}

        {loading ? (
          <p className="text-muted">Učitavam...</p>
        ) : (
          <div className="station-table-wrap">
            <table className="table vote-count-table">
              <thead>
                <tr>
                  <th>Šifra</th>
                  <th>Naziv</th>
                  <th>Županija</th>
                  <th>Regija</th>
                  <th className="text-end">Birači</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((s) => (
                  <tr key={s.id}>
                    <td>{s.code}</td>
                    <td>{s.name}</td>
                    <td className="text-muted">{s.zupanija || "-"}</td>
                    <td className="text-muted">{s.region || "-"}</td>
                    <td className="text-end">{s.registered_voters}</td>
                    <td>{s.status}</td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={6} className="text-muted">
                      Nema biračkih mjesta koja odgovaraju filteru.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

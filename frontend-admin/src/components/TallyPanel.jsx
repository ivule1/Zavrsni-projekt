import { useState } from "react";
import { ApiError, tallyElection } from "../api";
import { CHART_PALETTE } from "../chartPalette";
import BarChart from "./BarChart";
import BreakdownList from "./BreakdownList";
import DonutChart from "./DonutChart";
import StackedBarChart from "./StackedBarChart";

// "Rezultati po NUTS2 regiji/zupaniji" nisu samo "koliko je glasova palo u
// toj skupini" (to je izlaznost, ne rezultat) - svaki stupac je razbijen na
// segmente po kandidatu (ISTOM bojom kao "Rezultati po kandidatu" - vidi
// candidateColorById nize) da se odmah vidi i "koliko" i "tko". Poziva se s
// VEC sortiranim popisom (TallyPanel sortira opadajuce po total prije nego
// sto ga proslijedi i ovdje i u BreakdownList, da graf i popis ispod imaju
// isti redoslijed).
function buildStackedData(sortedGroups, candidateColorById) {
  return sortedGroups.map((g) => ({
    label: g.group,
    total: g.total,
    segments: g.by_candidate.map((c) => ({
      name: c.name,
      value: c.count,
      color: candidateColorById.get(c.candidate_id) || "#999",
    })),
  }));
}

export default function TallyPanel({ token, electionId }) {
  const [privateKey, setPrivateKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const handleTally = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await tallyElection(token, electionId, privateKey);
      setResult(data);
      // privatni kljuc se NE cuva nigdje (34.1) - cim smo dobili rezultat, brisemo ga iz
      // memorije ove komponente umjesto da ga ostavimo u polju/stanju
      setPrivateKey("");
    } catch (err) {
      setResult(null);
      setError(err instanceof ApiError ? err.message : "Neocekivana greska.");
    } finally {
      setLoading(false);
    }
  };

  // Ista boja za istog kandidata posvuda (donut, vertikalni stupci, segmenti
  // u StackedBarChart) - kljuc po candidate_id, redoslijed boja isti kao u
  // "Rezultati po kandidatu" (rezultati su vec sortirani po display_order,
  // vidi backend _by_candidate_list).
  const candidateColorById = result
    ? new Map(result.results.map((r, i) => [r.candidate_id, CHART_PALETTE[i % CHART_PALETTE.length]]))
    : null;
  const sortedByRegion = result ? [...result.by_region].sort((a, b) => b.total - a.total) : null;
  const sortedByZupanija = result ? [...result.by_zupanija].sort((a, b) => b.total - a.total) : null;

  return (
    <div className="admin-card">
      <h2 className="h5 mb-3">Brojanje glasova (Tally)</h2>

      {!result && (
        <form onSubmit={handleTally}>
          <p className="text-muted small mb-2">
            Unesi privatni ključ koji si dobio SAMO JEDNOM prilikom otvaranja ovog izbora. Ključ se
            koristi samo za ovaj jedan zahtjev i nigdje se ne sprema.
          </p>
          <textarea
            className="form-control mb-3"
            rows={6}
            style={{ fontFamily: "monospace", fontSize: "0.8rem" }}
            placeholder="-----BEGIN PRIVATE KEY-----..."
            value={privateKey}
            onChange={(e) => setPrivateKey(e.target.value)}
            disabled={loading}
            required
          />
          {error && <div className="alert alert-danger py-2">{error}</div>}
          <button type="submit" className="btn admin-btn text-white" disabled={loading || !privateKey.trim()}>
            {loading ? "Dešifriram..." : "Prebroji glasove"}
          </button>
        </form>
      )}

      {result && (
        <div>
          <div className="d-flex align-items-center gap-3 mb-3 flex-wrap">
            <span>
              Ukupno glasova: <strong>{result.total_votes}</strong>
            </span>
            {result.integrity_ok ? (
              <span className="integrity-ok">✓ integritet lanca potvrđen</span>
            ) : (
              <span className="integrity-bad">⚠ integritet lanca NIJE potvrđen - podaci su možda mijenjani</span>
            )}
          </div>

          {!result.integrity_ok && (
            <div className="tally-warning mb-3">
              Provjera integriteta (poglavlje 25 specifikacije) otkrila je da lanac hash-eva glasova
              nije ispravan. Rezultati su ipak izračunati, ali ovo treba istražiti prije objave
              konačnih rezultata.
            </div>
          )}

          <h3 className="h6 mt-4 mb-3">Rezultati po kandidatu</h3>
          <div className="d-flex flex-wrap gap-4 align-items-end mb-2">
            <DonutChart
              data={result.results.map((r, i) => ({
                label: r.name,
                value: r.count,
                color: CHART_PALETTE[i % CHART_PALETTE.length],
              }))}
            />
            {/* showLabels={false} - donut lijevo vec ima legendu s istim
                bojama/nazivima/postocima, pa stupci ovdje ne ponavljaju
                naziv ispod sebe (boja stupca vec govori o kojem je
                kandidatu rijec), samo tocan broj glasova iznad svakog. */}
            <BarChart
              showLabels={false}
              data={result.results.map((r, i) => ({
                label: r.name,
                value: r.count,
                color: CHART_PALETTE[i % CHART_PALETTE.length],
              }))}
            />
          </div>

          <h3 className="h6 mt-4 mb-3">Rezultati po NUTS2 regiji</h3>
          <div className="chart-legend-inline">
            {result.results.map((r, i) => (
              <span key={r.candidate_id} className="chart-legend-item">
                <span
                  className="chart-legend-swatch"
                  style={{ backgroundColor: CHART_PALETTE[i % CHART_PALETTE.length] }}
                />
                {r.name}
              </span>
            ))}
          </div>
          <StackedBarChart data={buildStackedData(sortedByRegion, candidateColorById)} />
          <BreakdownList
            groups={sortedByRegion}
            getKey={(g) => g.group}
            getLabel={(g) => g.group}
            getTotal={(g) => g.total}
            getByCandidate={(g) => g.by_candidate}
          />

          <h3 className="h6 mt-4 mb-3">Rezultati po županiji</h3>
          <div className="chart-legend-inline">
            {result.results.map((r, i) => (
              <span key={r.candidate_id} className="chart-legend-item">
                <span
                  className="chart-legend-swatch"
                  style={{ backgroundColor: CHART_PALETTE[i % CHART_PALETTE.length] }}
                />
                {r.name}
              </span>
            ))}
          </div>
          <StackedBarChart scrollable data={buildStackedData(sortedByZupanija, candidateColorById)} />
          <BreakdownList
            groups={sortedByZupanija}
            getKey={(g) => g.group}
            getLabel={(g) => g.group}
            getTotal={(g) => g.total}
            getByCandidate={(g) => g.by_candidate}
            maxHeight="40vh"
          />

          <h3 className="h6 mt-4 mb-3">Rezultati po biralištu</h3>
          <BreakdownList
            groups={result.by_station}
            getKey={(s) => s.station_id}
            getLabel={(s) => `${s.station_code} - ${s.station_name}`}
            getTotal={(s) => s.total}
            getByCandidate={(s) => s.by_candidate}
            maxHeight="40vh"
          />

          <button type="button" className="btn btn-outline-secondary btn-sm mt-4" onClick={() => setResult(null)}>
            Ponovno brojanje
          </button>
        </div>
      )}
    </div>
  );
}

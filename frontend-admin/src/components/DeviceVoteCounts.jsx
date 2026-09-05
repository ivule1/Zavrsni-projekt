import { useEffect, useRef, useState } from "react";
import { ApiError, getDeviceVoteCounts } from "../api";

// FAZA 9 (dopuna) - zadatak #16 stavka 6: prikaz broja glasova PO UREDJAJU
// (ne samo po biralistu) za odabrani izbor, izvor su audit_logs zapisi
// (VOTE_ACCEPTED s election_id u metapodacima) - poglavlje 34.2 (uredjaji su
// eksplicitno registrirani, nikad self-service) ovime dobiva i uvid u to
// koji je konkretan uredjaj na biralistu primio koliko glasova.
//
// `liveTotal` (opcionalno) - ukupan broj glasova IZVEDEN iz istog WS toka
// koji vec uzivo azurira "Glasovi po biralistu" u MonitorTab-u (drzi ga
// Dashboard.jsx). Ovaj prikaz dolazi iz zasebnog REST poziva (nema svoj WS
// event), pa bez ovoga ostaje "zamrznut" dok admin rucno ne klikne
// "Osvjezi". Kad se liveTotal promijeni, ponovno dohvacamo - s malom
// odgodom (debounce) da ne saljemo zahtjev za BAS SVAKI pojedinacni glas
// nego se "smiri" nakratko nakon naleta glasova.
export default function DeviceVoteCounts({ token, electionId, liveTotal }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef(null);

  const load = () => {
    if (!electionId) return;
    setLoading(true);
    setError("");
    getDeviceVoteCounts(token, electionId)
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Greška pri učitavanju broja glasova po uređaju."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    setData(null);
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [electionId]);

  useEffect(() => {
    if (!electionId || liveTotal === undefined || liveTotal === null) return;
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(load, 600);
    return () => clearTimeout(debounceRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liveTotal, electionId]);

  if (!electionId) return null;

  return (
    <details className="admin-card collapsible-card">
      <summary>
        <span className="h5 mb-0">Glasovi po uređaju</span>
        <span className="d-flex align-items-center gap-2">
          {data && (
            <span>
              Ukupno: <strong>{data.total_votes}</strong>
            </span>
          )}
          <button
            type="button"
            className="btn btn-outline-secondary btn-sm"
            // Gumb je unutar <summary>, pa bi klik inace (uz osvjezavanje
            // podataka) i otvorio/zatvorio karticu - preventDefault sprijeci
            // taj toggle da "Osvjezi" radi neovisno o tome je li kartica
            // trenutno rasklopljena.
            onClick={(e) => {
              e.preventDefault();
              load();
            }}
            disabled={loading}
          >
            {loading ? "Osvježavam..." : "Osvježi"}
          </button>
        </span>
      </summary>

      <div className="collapsible-card-body">
        {error && <div className="alert alert-danger py-2">{error}</div>}

        {data && (
          <table className="table vote-count-table">
            <thead>
              <tr>
                <th>Biralište</th>
                <th>Uređaj</th>
                <th className="text-end">Broj glasova</th>
              </tr>
            </thead>
            <tbody>
              {data.devices.map((d) => (
                <tr key={d.device_id}>
                  <td>{d.station_code}</td>
                  <td>{d.device_code}</td>
                  <td className="text-end vote-count-cell">{d.count}</td>
                </tr>
              ))}
              {data.devices.length === 0 && (
                <tr>
                  <td colSpan={3} className="text-muted">
                    Za ovaj izbor još nema zabilježenih glasova po uređajima.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </details>
  );
}

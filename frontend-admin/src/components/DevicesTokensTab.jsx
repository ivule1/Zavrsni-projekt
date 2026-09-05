import { useEffect, useState } from "react";
import {
  ApiError,
  bulkGenerateTokens,
  bulkRegisterDevices,
  generateTokens,
  getTokenSummary,
  listDevices,
  listStations,
  registerDevice,
} from "../api";

function BulkDevicesCard({ token }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const handleRun = async () => {
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const data = await bulkRegisterDevices(token, null, true);
      setResult(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Greška pri registraciji uređaja.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="admin-card">
      <h2 className="h5 mb-2">Uređaji - postavljanje jednim klikom</h2>
      <p className="text-muted small mb-3">
        Registrira po jedan uređaj na svako aktivno biralište koje ga još nema. Birališta koja već imaju
        uređaj se preskaču - siguran je za ponovno pokretanje.
      </p>
      <button type="button" className="btn admin-btn text-white" onClick={handleRun} disabled={busy}>
        {busy ? "Registriram..." : "Registriraj uređaje na sva birališta bez uređaja"}
      </button>
      {error && <div className="alert alert-danger py-2 mt-3 mb-0">{error}</div>}
      {result && (
        <div className="alert alert-success py-2 mt-3 mb-0">
          Registrirano {result.created.length} novih uređaja, preskočeno {result.skipped_station_ids.length}{" "}
          (već su imali uređaj). Svaki API ključ prikazan je samo ovaj put - dolje u tablici.
          {result.created.length > 0 && (
            <div className="station-table-wrap mt-2">
              <table className="table vote-count-table mb-0">
                <thead>
                  <tr>
                    <th>Biralište</th>
                    <th>Šifra uređaja</th>
                    <th>API ključ</th>
                  </tr>
                </thead>
                <tbody>
                  {result.created.map((item) => (
                    <tr key={item.device.id}>
                      <td>{item.station_code}</td>
                      <td>{item.device.device_code}</td>
                      <td style={{ fontFamily: "monospace", fontSize: "0.75rem" }}>{item.api_key}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function BulkTokensCard({ token }) {
  const [count, setCount] = useState("");
  const [force, setForce] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const handleRun = async () => {
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const data = await bulkGenerateTokens(token, null, count ? parseInt(count, 10) : null, force);
      setResult(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Greška pri generiranju tokena.");
    } finally {
      setBusy(false);
    }
  };

  // Sirovi tokeni se vracaju iz backenda SAMO u ovom jednom odgovoru (RULE 04
  // - baza cuva samo hash), pa admin mora imati nacin da ih odmah pregleda
  // ili preuzme za ispis/podjelu po biralistima - prije ovog popravka
  // rezultat je bio dohvacen ali NIKAD prikazan na ekranu.
  const handleDownload = () => {
    if (!result || result.generated.length === 0) return;
    const lines = result.generated.flatMap((s) => [
      `# ${s.station_code} (${s.count} tokena)`,
      ...s.tokens,
      "",
    ]);
    const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tokeni-${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="admin-card">
      <h2 className="h5 mb-2">Tokeni - postavljanje jednim klikom</h2>
      <p className="text-muted small mb-3">
        Generira pool tokena za svako aktivno biralište koje ga još nema (broj tokena po biralištu, ako se
        ne unese, jednak je broju registriranih birača te stanice).
      </p>
      <div className="d-flex gap-2 align-items-end flex-wrap mb-3">
        <div>
          <label className="form-label small">Broj tokena po biralištu (opcionalno)</label>
          <input
            type="number"
            min={1}
            className="form-control"
            style={{ width: "220px" }}
            value={count}
            onChange={(e) => setCount(e.target.value)}
            placeholder="npr. 300"
            disabled={busy}
          />
        </div>
        <div className="form-check mb-2">
          <input
            type="checkbox"
            className="form-check-input"
            id="forceTokens"
            checked={force}
            onChange={(e) => setForce(e.target.checked)}
            disabled={busy}
          />
          <label className="form-check-label" htmlFor="forceTokens">
            Generiraj dodatno i za birališta koja već imaju pool
          </label>
        </div>
      </div>
      <button type="button" className="btn admin-btn text-white" onClick={handleRun} disabled={busy}>
        {busy ? "Generiram..." : "Generiraj tokene za sva birališta"}
      </button>
      {error && <div className="alert alert-danger py-2 mt-3 mb-0">{error}</div>}
      {result && (
        <div className="alert alert-success py-2 mt-3 mb-0">
          <p className="mb-2">
            Generirani poolovi za {result.generated.length} birališta, preskočeno{" "}
            {result.skipped_station_ids.length} (već imaju pool, force nije uključen). Tokeni se prikazuju
            SAMO ovaj put - preuzmi ih odmah ako trebaju ispis.
          </p>
          {result.generated.length > 0 && (
            <>
              <button type="button" className="btn btn-outline-secondary btn-sm mb-2" onClick={handleDownload}>
                Preuzmi sve kao .txt
              </button>
              <div style={{ maxHeight: "40vh", overflowY: "auto" }}>
                {result.generated.map((s) => (
                  <details key={s.station_id} className="mb-1">
                    <summary className="small">
                      {s.station_code} — {s.count} tokena
                    </summary>
                    <textarea
                      className="form-control mt-1"
                      rows={Math.min(s.tokens.length, 8)}
                      readOnly
                      style={{ fontFamily: "monospace", fontSize: "0.7rem" }}
                      value={s.tokens.join("\n")}
                      onFocus={(e) => e.target.select()}
                    />
                  </details>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function SingleStationPanel({ token, stations }) {
  const [stationId, setStationId] = useState("");
  const [devices, setDevices] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [newDeviceCode, setNewDeviceCode] = useState("");
  const [busyDevice, setBusyDevice] = useState(false);
  const [newDeviceKey, setNewDeviceKey] = useState(null);

  const [tokenCount, setTokenCount] = useState("");
  const [tokenForce, setTokenForce] = useState(false);
  const [busyTokens, setBusyTokens] = useState(false);
  const [newTokens, setNewTokens] = useState(null);

  const station = stations.find((s) => s.id === stationId) || null;

  const reload = () => {
    if (!stationId) return;
    setLoading(true);
    setError("");
    Promise.all([listDevices(token, stationId), getTokenSummary(token, stationId)])
      .then(([deviceList, tokenSummary]) => {
        setDevices(deviceList);
        setSummary(tokenSummary);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Greška pri učitavanju."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    setNewDeviceKey(null);
    setNewTokens(null);
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stationId]);

  const handleAddDevice = async (event) => {
    event.preventDefault();
    if (!newDeviceCode.trim()) return;
    setBusyDevice(true);
    setError("");
    try {
      const data = await registerDevice(token, stationId, newDeviceCode.trim());
      setNewDeviceKey(data.api_key);
      setNewDeviceCode("");
      reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Greška pri registraciji uređaja.");
    } finally {
      setBusyDevice(false);
    }
  };

  const handleGenerateTokens = async (event) => {
    event.preventDefault();
    setBusyTokens(true);
    setError("");
    try {
      const data = await generateTokens(token, stationId, tokenCount ? parseInt(tokenCount, 10) : null, tokenForce);
      setNewTokens(data.tokens);
      reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Greška pri generiranju tokena.");
    } finally {
      setBusyTokens(false);
    }
  };

  return (
    <div className="admin-card">
      <h2 className="h5 mb-3">Pojedinačno biralište</h2>
      <select className="form-select mb-3" value={stationId} onChange={(e) => setStationId(e.target.value)}>
        <option value="">Odaberi biralište...</option>
        {stations.map((s) => (
          <option key={s.id} value={s.id}>
            {s.code} - {s.name}
          </option>
        ))}
      </select>

      {error && <div className="alert alert-danger py-2">{error}</div>}

      {stationId && (
        <>
          {station && (
            <p className="text-muted small mb-3">
              {station.zupanija || "bez županije"}
              {station.region ? ` · ${station.region}` : ""} · {station.registered_voters} registriranih birača
            </p>
          )}
          {loading ? (
            <p className="text-muted">Učitavam...</p>
          ) : (
            <div className="row g-3">
              <div className="col-md-6">
                <h3 className="h6">Uređaji ({devices.length})</h3>
                <ul className="list-unstyled small mb-2">
                  {devices.map((d) => (
                    <li key={d.id}>
                      {d.device_code} <span className="text-muted">({d.status})</span>
                    </li>
                  ))}
                  {devices.length === 0 && <li className="text-muted">Nema registriranih uređaja.</li>}
                </ul>
                <form onSubmit={handleAddDevice} className="d-flex gap-2">
                  <input
                    className="form-control form-control-sm"
                    placeholder="Šifra novog uređaja"
                    value={newDeviceCode}
                    onChange={(e) => setNewDeviceCode(e.target.value)}
                    disabled={busyDevice}
                  />
                  <button type="submit" className="btn admin-btn text-white btn-sm text-nowrap" disabled={busyDevice}>
                    Dodaj
                  </button>
                </form>
                {newDeviceKey && (
                  <div className="alert alert-success py-2 mt-2 mb-0 small">
                    API ključ (prikazan samo ovaj put): <br />
                    <code>{newDeviceKey}</code>
                  </div>
                )}
              </div>

              <div className="col-md-6">
                <h3 className="h6">Tokeni</h3>
                {summary && (
                  <p className="small mb-2">
                    Ukupno: <strong>{summary.total}</strong> · Dostupno: <strong>{summary.available}</strong> ·
                    Iskorišteno: <strong>{summary.used}</strong>
                  </p>
                )}
                <form onSubmit={handleGenerateTokens} className="mb-2">
                  <div className="d-flex gap-2 mb-2">
                    <input
                      type="number"
                      min={1}
                      className="form-control form-control-sm"
                      placeholder="Broj (default = broj birača)"
                      value={tokenCount}
                      onChange={(e) => setTokenCount(e.target.value)}
                      disabled={busyTokens}
                    />
                    <button type="submit" className="btn admin-btn text-white btn-sm text-nowrap" disabled={busyTokens}>
                      Generiraj
                    </button>
                  </div>
                  <div className="form-check">
                    <input
                      type="checkbox"
                      className="form-check-input"
                      id="tokenForceSingle"
                      checked={tokenForce}
                      onChange={(e) => setTokenForce(e.target.checked)}
                      disabled={busyTokens}
                    />
                    <label className="form-check-label small" htmlFor="tokenForceSingle">
                      Generiraj i ako pool već postoji
                    </label>
                  </div>
                </form>
                {newTokens && (
                  <div className="alert alert-success py-2 mb-0 small">
                    Generirano {newTokens.length} tokena (prikazani samo ovaj put):
                    <textarea
                      className="form-control mt-1"
                      rows={4}
                      readOnly
                      style={{ fontFamily: "monospace", fontSize: "0.7rem" }}
                      value={newTokens.join("\n")}
                      onFocus={(e) => e.target.select()}
                    />
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function DevicesTokensTab({ token }) {
  const [stations, setStations] = useState([]);

  useEffect(() => {
    listStations(token)
      .then(setStations)
      .catch(() => {
        // greska se vec prikazuje na kartici Biralista - ovdje samo tiho ostavi prazan popis
      });
  }, [token]);

  return (
    <div>
      <BulkDevicesCard token={token} />
      <BulkTokensCard token={token} />
      <SingleStationPanel token={token} stations={stations} />
    </div>
  );
}

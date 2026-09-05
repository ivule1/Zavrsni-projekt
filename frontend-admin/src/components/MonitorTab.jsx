import DeviceVoteCounts from "./DeviceVoteCounts";
import SecurityEventsPanel from "./SecurityEventsPanel";
import TallyPanel from "./TallyPanel";
import TurnoutPanel from "./TurnoutPanel";

const STATUS_LABEL = {
  DRAFT: "Nije otvoren",
  OPEN: "Otvoren",
  CLOSED: "Zatvoren",
};

export default function MonitorTab({
  token,
  elections,
  selectedElectionId,
  setSelectedElectionId,
  selectedElection,
  voteCounts,
  flashStation,
}) {
  return (
    <div>
      <div className="admin-card">
        <label className="form-label" htmlFor="electionSelect">
          Izbor
        </label>
        <select
          id="electionSelect"
          className="form-select"
          value={selectedElectionId}
          onChange={(e) => setSelectedElectionId(e.target.value)}
        >
          {elections.length === 0 && <option value="">Nema izbora</option>}
          {elections.map((e) => (
            <option key={e.id} value={e.id}>
              {e.name}
            </option>
          ))}
        </select>
        {selectedElection && (
          <span className={`status-badge status-${selectedElection.status.toLowerCase()} mt-2 d-inline-block`}>
            {STATUS_LABEL[selectedElection.status] || selectedElection.status}
          </span>
        )}
      </div>

      {voteCounts && (
        <details className="admin-card collapsible-card">
          <summary>
            <span className="h5 mb-0">Glasovi po biralištu</span>
            <span>
              Ukupno: <strong>{voteCounts.total_votes}</strong>
            </span>
          </summary>
          <div className="collapsible-card-body">
            <table className="table vote-count-table">
              <thead>
                <tr>
                  <th>Biralište</th>
                  <th className="text-end">Broj glasova</th>
                </tr>
              </thead>
              <tbody>
                {voteCounts.stations.map((s) => (
                  <tr key={s.station_id} className={flashStation === s.station_id ? "count-flash" : ""}>
                    <td>{s.station_code}</td>
                    <td className="text-end vote-count-cell">{s.count}</td>
                  </tr>
                ))}
                {voteCounts.stations.length === 0 && (
                  <tr>
                    <td colSpan={2} className="text-muted">
                      Nema registriranih biračkih mjesta.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </details>
      )}

      {selectedElection && (
        <DeviceVoteCounts token={token} electionId={selectedElection.id} liveTotal={voteCounts?.total_votes} />
      )}

      <SecurityEventsPanel token={token} />

      {selectedElection?.status === "OPEN" && voteCounts && (
        <TurnoutPanel token={token} voteCounts={voteCounts} />
      )}

      {selectedElection?.status === "CLOSED" && <TallyPanel token={token} electionId={selectedElection.id} />}
    </div>
  );
}

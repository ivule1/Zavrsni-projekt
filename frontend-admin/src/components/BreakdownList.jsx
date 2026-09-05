// Popis grupa (biralista / zupanije / regije) s trakama razmjernim udjelu u
// ukupnom broju glasova - u istom stilu kao postojece progress trake u
// TallyPanelu. Svaki redak se moze rasklopiti (<details>) i pokazati
// razdiobu po kandidatu unutar te grupe, bez dodatnog stanja u JS-u.
//
// showDetails=false (FAZA 9 dopuna - izlaznost uzivo dok je izbor OTVOREN):
// iscrtava isti red BEZ <details>/<summary> rasklapanja i BEZ ikakvog poziva
// na getByCandidate - dok je izbor otvoren, razdioba po kandidatu ne smije
// biti ni prikazana ni izvediva (glasovi se ne mogu dekriptirati prije
// zatvaranja izbora, poglavlje 34.1), pa ova varijanta namjerno nema nacina
// da tu podjelu uopce dohvati, umjesto da samo sakrije prazan gumb za
// rasklapanje.
export default function BreakdownList({
  groups,
  getKey,
  getLabel,
  getTotal,
  getByCandidate,
  getSubLabel,
  maxHeight,
  showDetails = true,
}) {
  const maxTotal = Math.max(1, ...groups.map((g) => getTotal(g)));

  if (!showDetails) {
    return (
      <div className="breakdown-list" style={maxHeight ? { maxHeight, overflowY: "auto" } : undefined}>
        {groups.length === 0 && <p className="text-muted small mb-0">Nema podataka.</p>}
        {groups.map((g) => {
          const total = getTotal(g);
          return (
            <div key={getKey(g)} className="breakdown-row breakdown-row--plain">
              <span className="breakdown-label">{getLabel(g)}</span>
              <span className="breakdown-bar-wrap">
                <span className="breakdown-bar" style={{ width: `${(total / maxTotal) * 100}%` }} />
              </span>
              {getSubLabel && <span className="breakdown-sublabel">{getSubLabel(g)}</span>}
              <span className="breakdown-total">{total}</span>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className="breakdown-list" style={maxHeight ? { maxHeight, overflowY: "auto" } : undefined}>
      {groups.length === 0 && <p className="text-muted small mb-0">Nema podataka.</p>}
      {groups.map((g) => {
        const total = getTotal(g);
        const byCandidate = getByCandidate(g);
        // Pobjednik UNUTAR ove grupe (npr. na ovom biralistu/zupaniji) -
        // ne mora biti isti kao ukupni pobjednik izbora. maxCount > 0 cuva
        // od boldiranja "pobjednika" kad grupa uopce nema glasova (svi 0).
        const maxCount = Math.max(0, ...byCandidate.map((c) => c.count));
        return (
          <details key={getKey(g)} className="breakdown-row">
            <summary>
              <span className="breakdown-label">{getLabel(g)}</span>
              <span className="breakdown-bar-wrap">
                <span
                  className="breakdown-bar"
                  style={{ width: `${(total / maxTotal) * 100}%` }}
                />
              </span>
              {getSubLabel && <span className="breakdown-sublabel">{getSubLabel(g)}</span>}
              <span className="breakdown-total">{total}</span>
            </summary>
            <ul className="breakdown-detail">
              {byCandidate.map((c) => (
                <li
                  key={c.candidate_id}
                  className={maxCount > 0 && c.count === maxCount ? "breakdown-detail-winner" : undefined}
                >
                  <span>{c.name}</span>
                  <span className="vote-count-cell">{c.count}</span>
                </li>
              ))}
            </ul>
          </details>
        );
      })}
    </div>
  );
}

export default function CandidateSelectScreen({
  electionName,
  candidates,
  selected,
  onSelect,
  onContinue,
}) {
  return (
    <div className="text-center w-100">
      <h1 className="kiosk-title mb-2">IZABERITE KANDIDATA</h1>
      {electionName && <p className="kiosk-subtitle mb-4">{electionName}</p>}

      <div className="d-grid gap-3 mb-4">
        {candidates.map((candidate) => (
          <button
            key={candidate.id}
            type="button"
            className={`kiosk-candidate-card${selected?.id === candidate.id ? " selected" : ""}`}
            onClick={() => onSelect(candidate)}
          >
            <span>{candidate.name}</span>
            {selected?.id === candidate.id && <span className="kiosk-check">✓</span>}
          </button>
        ))}
      </div>

      <button
        type="button"
        className="btn btn-primary btn-lg kiosk-btn w-100"
        disabled={!selected}
        onClick={onContinue}
      >
        NASTAVI
      </button>
    </div>
  );
}

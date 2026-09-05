export default function ConfirmScreen({ candidate, loading, onConfirm, onBack }) {
  return (
    <div className="text-center w-100">
      <h1 className="kiosk-title mb-4">POTVRDA GLASA</h1>
      <p className="kiosk-subtitle mb-2">Glasali ste za:</p>
      <p className="kiosk-candidate-name mb-5">{candidate?.name}</p>

      <button
        type="button"
        className="btn btn-primary btn-lg kiosk-btn w-100 mb-3"
        onClick={onConfirm}
        disabled={loading}
      >
        {loading ? "SPREMANJE..." : "POTVRDI GLAS"}
      </button>
      <button type="button" className="btn btn-link kiosk-link" onClick={onBack} disabled={loading}>
        Promijeni izbor
      </button>
    </div>
  );
}

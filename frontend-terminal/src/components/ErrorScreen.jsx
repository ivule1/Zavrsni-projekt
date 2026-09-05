export default function ErrorScreen({ message, onRetry }) {
  return (
    <div className="text-center w-100">
      <div className="kiosk-error-icon mb-4">!</div>
      <h1 className="kiosk-title mb-3">GREŠKA</h1>
      <p className="kiosk-subtitle mb-5">{message}</p>
      <button type="button" className="btn btn-primary btn-lg kiosk-btn w-100" onClick={onRetry}>
        POKUŠAJ PONOVNO
      </button>
    </div>
  );
}

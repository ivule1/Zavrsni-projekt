import { useState } from "react";

// Isti format kao backend generira (Base32, grupe od 5 znakova) - poglavlje 34.5
function formatToken(raw) {
  const cleaned = raw.toUpperCase().replace(/[^A-Z2-7]/g, "");
  return cleaned.match(/.{1,5}/g)?.join("-") ?? cleaned;
}

export default function TokenEntryScreen({ onSubmit, loading }) {
  const [value, setValue] = useState("");

  const handleChange = (event) => {
    setValue(formatToken(event.target.value));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    if (value.trim().length > 0) {
      onSubmit(value);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="text-center w-100">
      <h1 className="kiosk-title mb-4">UNESITE GLASAČKI KLJUČ</h1>
      <input
        type="text"
        inputMode="text"
        className="form-control form-control-lg kiosk-token-input text-center mb-4"
        value={value}
        onChange={handleChange}
        placeholder="XXXXX-XXXXX-XXXXX"
        autoFocus
        disabled={loading}
      />
      <button
        type="submit"
        className="btn btn-primary btn-lg kiosk-btn w-100"
        disabled={loading || value.trim().length === 0}
      >
        {loading ? "PROVJERA U TIJEKU..." : "POTVRDI KLJUČ"}
      </button>
    </form>
  );
}

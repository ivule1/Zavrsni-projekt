# Provjera razvojne okoline za projekt e-glasanja
# Pokreni: powershell -ExecutionPolicy Bypass -File check_environment.ps1

$tools = @(
    @{ Name = "Git";              Cmd = "git";    Args = "--version" },
    @{ Name = "Python";           Cmd = "python"; Args = "--version" },
    @{ Name = "pip";              Cmd = "pip";    Args = "--version" },
    @{ Name = "Node.js";          Cmd = "node";   Args = "--version" },
    @{ Name = "npm";              Cmd = "npm";    Args = "--version" },
    @{ Name = "PostgreSQL (psql)"; Cmd = "psql";  Args = "--version" }
)

Write-Host "=== Provjera razvojne okoline za e-glasanje projekt ===" -ForegroundColor Cyan
Write-Host ""

foreach ($t in $tools) {
    $found = Get-Command $t.Cmd -ErrorAction SilentlyContinue
    if ($found) {
        $version = & $t.Cmd $t.Args 2>&1
        Write-Host ("{0,-20} OK  -> {1}" -f $t.Name, $version) -ForegroundColor Green
    } else {
        Write-Host ("{0,-20} NIJE PRONADJEN (nije instaliran ili nije u PATH-u)" -f $t.Name) -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Kopiraj cijeli output iznad i posalji ga natrag u chat." -ForegroundColor Cyan

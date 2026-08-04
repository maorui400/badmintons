$ErrorActionPreference = 'Stop'

Write-Host 'Volcengine Ark API Key Setup' -ForegroundColor Cyan
Write-Host 'Copy only the API Key value and paste it here. Input is hidden.'
Write-Host ''

$secureValue = Read-Host 'Paste ARK API Key' -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureValue)
try {
    $plainValue = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr).Trim()
    if ($plainValue.Length -lt 20) {
        throw 'The API Key is too short.'
    }
    if ($plainValue -notmatch '^[A-Za-z0-9._-]+$') {
        throw 'The API Key contains spaces or non-ASCII characters. Copy only the key value.'
    }

    [Environment]::SetEnvironmentVariable('ARK_API_KEY', $plainValue, 'User')
    $savedValue = [Environment]::GetEnvironmentVariable('ARK_API_KEY', 'User')
    if ([string]::IsNullOrWhiteSpace($savedValue)) {
        throw 'ARK_API_KEY was not saved to the Windows User environment.'
    }

    Write-Host "ARK_API_KEY saved successfully (length: $($savedValue.Length))" -ForegroundColor Green
}
finally {
    if ($bstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
    $plainValue = $null
    $savedValue = $null
    $secureValue = $null
}

Write-Host ''
Write-Host 'Setup complete. Return to Codex.' -ForegroundColor Cyan
Read-Host 'Press Enter to close'

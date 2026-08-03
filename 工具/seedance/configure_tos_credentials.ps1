$ErrorActionPreference = 'Stop'

function Read-And-SaveSecret {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Prompt,

        [Parameter(Mandatory = $true)]
        [string]$EnvironmentName
    )

    $secureValue = Read-Host $Prompt -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureValue)
    try {
        $plainValue = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr).Trim()
        if ($plainValue.Length -lt 10) {
            throw "$EnvironmentName input is invalid. Run this tool again."
        }

        [Environment]::SetEnvironmentVariable($EnvironmentName, $plainValue, 'User')
        $savedValue = [Environment]::GetEnvironmentVariable($EnvironmentName, 'User')
        if ([string]::IsNullOrWhiteSpace($savedValue)) {
            throw "$EnvironmentName was not saved to the Windows User environment."
        }

        Write-Host "$EnvironmentName saved successfully (length: $($savedValue.Length))" -ForegroundColor Green
    }
    finally {
        if ($bstr -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
        $plainValue = $null
        $savedValue = $null
        $secureValue = $null
    }
}

Write-Host 'TOS Credential Setup' -ForegroundColor Cyan
Write-Host 'Copy each value from Volcengine IAM and paste it here. Input is hidden.'
Write-Host ''

Read-And-SaveSecret -Prompt 'Paste Access Key (AK)' -EnvironmentName 'TOS_ACCESS_KEY'
Read-And-SaveSecret -Prompt 'Paste Secret Access Key (SK)' -EnvironmentName 'TOS_SECRET_KEY'

Write-Host ''
Write-Host 'Setup complete. Return to Codex.' -ForegroundColor Cyan
Read-Host 'Press Enter to close'

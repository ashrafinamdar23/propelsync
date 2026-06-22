param(
    [string]$CommonName = "localhost",
    [string[]]$DnsName = @("localhost"),
    [string[]]$IpAddress = @("127.0.0.1"),
    [int]$ValidDays = 825,
    [string]$OutputDirectory = "$PSScriptRoot\..\certs"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $OutputDirectory)) {
    New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
}

$rsa = [System.Security.Cryptography.RSA]::Create(2048)
$subject = [System.Security.Cryptography.X509Certificates.X500DistinguishedName]::new("CN=$CommonName")
$request = [System.Security.Cryptography.X509Certificates.CertificateRequest]::new(
    $subject,
    $rsa,
    [System.Security.Cryptography.HashAlgorithmName]::SHA256,
    [System.Security.Cryptography.RSASignaturePadding]::Pkcs1
)

$sanBuilder = [System.Security.Cryptography.X509Certificates.SubjectAlternativeNameBuilder]::new()
foreach ($name in $DnsName) {
    if ($name) {
        $sanBuilder.AddDnsName($name)
    }
}
foreach ($address in $IpAddress) {
    if ($address) {
        $sanBuilder.AddIpAddress([System.Net.IPAddress]::Parse($address))
    }
}

$request.CertificateExtensions.Add($sanBuilder.Build())
$request.CertificateExtensions.Add(
    [System.Security.Cryptography.X509Certificates.X509BasicConstraintsExtension]::new($false, $false, 0, $true)
)
$request.CertificateExtensions.Add(
    [System.Security.Cryptography.X509Certificates.X509KeyUsageExtension]::new(
        [System.Security.Cryptography.X509Certificates.X509KeyUsageFlags]::DigitalSignature -bor
            [System.Security.Cryptography.X509Certificates.X509KeyUsageFlags]::KeyEncipherment,
        $true
    )
)
$serverAuthOid = [System.Security.Cryptography.Oid]::new("1.3.6.1.5.5.7.3.1")
$enhancedUsages = [System.Security.Cryptography.OidCollection]::new()
[void]$enhancedUsages.Add($serverAuthOid)
$request.CertificateExtensions.Add(
    [System.Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension]::new($enhancedUsages, $true)
)

$notBefore = [System.DateTimeOffset]::UtcNow.AddMinutes(-5)
$notAfter = $notBefore.AddDays($ValidDays)
$certificate = $request.CreateSelfSigned($notBefore, $notAfter)

$certPath = Join-Path $OutputDirectory "propelsync-selfsigned.crt"
$keyPath = Join-Path $OutputDirectory "propelsync-selfsigned.key"

function Write-AsnLength {
    param(
        [System.IO.MemoryStream]$Stream,
        [int]$Length
    )

    if ($Length -lt 128) {
        $Stream.WriteByte($Length)
        return
    }

    $bytes = [System.BitConverter]::GetBytes($Length)
    [Array]::Reverse($bytes)
    $firstNonZero = 0
    while ($firstNonZero -lt $bytes.Length -and $bytes[$firstNonZero] -eq 0) {
        $firstNonZero++
    }
    $lengthBytes = $bytes[$firstNonZero..($bytes.Length - 1)]
    $Stream.WriteByte(0x80 -bor $lengthBytes.Length)
    $Stream.Write($lengthBytes, 0, $lengthBytes.Length)
}

function Write-DerInteger {
    param(
        [System.IO.MemoryStream]$Stream,
        [byte[]]$Value
    )

    $bytes = $Value
    while ($bytes.Length -gt 1 -and $bytes[0] -eq 0) {
        $bytes = $bytes[1..($bytes.Length - 1)]
    }
    if (($bytes[0] -band 0x80) -ne 0) {
        $bytes = [byte[]](0) + $bytes
    }

    $Stream.WriteByte(0x02)
    Write-AsnLength -Stream $Stream -Length $bytes.Length
    $Stream.Write($bytes, 0, $bytes.Length)
}

function Convert-RsaPrivateKeyToPem {
    param([System.Security.Cryptography.RSAParameters]$Parameters)

    $body = [System.IO.MemoryStream]::new()
    Write-DerInteger -Stream $body -Value ([byte[]](0))
    Write-DerInteger -Stream $body -Value $Parameters.Modulus
    Write-DerInteger -Stream $body -Value $Parameters.Exponent
    Write-DerInteger -Stream $body -Value $Parameters.D
    Write-DerInteger -Stream $body -Value $Parameters.P
    Write-DerInteger -Stream $body -Value $Parameters.Q
    Write-DerInteger -Stream $body -Value $Parameters.DP
    Write-DerInteger -Stream $body -Value $Parameters.DQ
    Write-DerInteger -Stream $body -Value $Parameters.InverseQ

    $bodyBytes = $body.ToArray()
    $sequence = [System.IO.MemoryStream]::new()
    $sequence.WriteByte(0x30)
    Write-AsnLength -Stream $sequence -Length $bodyBytes.Length
    $sequence.Write($bodyBytes, 0, $bodyBytes.Length)

    $pem = "-----BEGIN RSA PRIVATE KEY-----`n"
    $pem += [Convert]::ToBase64String($sequence.ToArray(), [System.Base64FormattingOptions]::InsertLineBreaks)
    $pem += "`n-----END RSA PRIVATE KEY-----`n"
    return $pem
}

$certPem = "-----BEGIN CERTIFICATE-----`n"
$certPem += [Convert]::ToBase64String($certificate.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert), [System.Base64FormattingOptions]::InsertLineBreaks)
$certPem += "`n-----END CERTIFICATE-----`n"

$keyPem = Convert-RsaPrivateKeyToPem -Parameters $rsa.ExportParameters($true)

Set-Content -LiteralPath $certPath -Value $certPem -NoNewline -Encoding ascii
Set-Content -LiteralPath $keyPath -Value $keyPem -NoNewline -Encoding ascii

Write-Host "Created $certPath"
Write-Host "Created $keyPath"

# Entirely synthetic vectors. No files, accounts, or captured materials are read.
$ErrorActionPreference = 'Stop'
function Assert-EqualBytes([byte[]]$actual, [byte[]]$expected, [string]$name) {
    if ([Convert]::ToHexString($actual) -cne [Convert]::ToHexString($expected)) { throw $name }
}
function Transform-Aes([byte[]]$data, [byte[]]$key, [byte[]]$iv, [string]$mode, [bool]$encrypt, [string]$padding) {
    $aes = [Security.Cryptography.Aes]::Create()
    try {
        $aes.Key = $key
        $aes.Mode = [Security.Cryptography.CipherMode]::$mode
        $aes.Padding = [Security.Cryptography.PaddingMode]::$padding
        if ($mode -eq 'CBC') { $aes.IV = $iv }
        $op = if ($encrypt) { $aes.CreateEncryptor() } else { $aes.CreateDecryptor() }
        try { return ,$op.TransformFinalBlock($data, 0, $data.Length) } finally { $op.Dispose() }
    } finally { $aes.Dispose() }
}
# NIST AES-128 ECB primitive vector (public standard test values, not account secrets).
$key = [Convert]::FromHexString('000102030405060708090A0B0C0D0E0F')
$plain = [Convert]::FromHexString('00112233445566778899AABBCCDDEEFF')
$cipher = Transform-Aes $plain $key @() 'ECB' $true 'None'
Assert-EqualBytes $cipher ([Convert]::FromHexString('69C4E0D86A7B0430D8CDB78070B4C55A')) 'AES ECB primitive'
# DAT algorithm: aligned 16-byte plaintext requires a full 16-byte PKCS7 block.
$datCipher = Transform-Aes $plain $key @() 'ECB' $true 'PKCS7'
if ($datCipher.Length -ne 32) { throw 'DAT padded length' }
Assert-EqualBytes (Transform-Aes $datCipher $key @() 'ECB' $false 'PKCS7') $plain 'DAT roundtrip'
# Emoticon CBC uses IV equal to the key; synthetic vector only.
$emojiCipher = Transform-Aes $plain $key $key 'CBC' $true 'PKCS7'
Assert-EqualBytes (Transform-Aes $emojiCipher $key $key 'CBC' $false 'PKCS7') $plain 'emoji roundtrip'
# Main database first page: salt + 4000 ciphertext + 16 IV + 64 MAC.
$raw = [byte[]](0..31)
$salt = [byte[]](0..15)
$derive = [Security.Cryptography.Rfc2898DeriveBytes]::new($raw, $salt, 256000, [Security.Cryptography.HashAlgorithmName]::SHA512)
try { $dbKey = $derive.GetBytes(32) } finally { $derive.Dispose() }
$macSalt = [byte[]]($salt | ForEach-Object { $_ -bxor 0x3a })
$derive = [Security.Cryptography.Rfc2898DeriveBytes]::new($dbKey, $macSalt, 2, [Security.Cryptography.HashAlgorithmName]::SHA512)
try { $macKey = $derive.GetBytes(32) } finally { $derive.Dispose() }
$body = [byte[]]::new(4000)
for ($i=0; $i -lt $body.Length; $i++) { $body[$i] = $i % 251 }
$iv = [byte[]](16..31)
$enc = Transform-Aes $body $dbKey $iv 'CBC' $true 'None'
$signed = [byte[]]($enc + $iv + [byte[]](1,0,0,0))
$hmac = [Security.Cryptography.HMACSHA512]::new($macKey)
try {
    $tag = $hmac.ComputeHash($signed)
    $page = [byte[]]($salt + $enc + $iv + $tag)
    if ($page.Length -ne 4096) { throw 'page length' }
    Assert-EqualBytes ($hmac.ComputeHash([byte[]]($page[16..4031] + [byte[]](1,0,0,0)))) $tag 'page HMAC'
    Assert-EqualBytes (Transform-Aes ([byte[]]$page[16..4015]) $dbKey ([byte[]]$page[4016..4031]) 'CBC' $false 'None') $body 'page body'
    $signed[0] = $signed[0] -bxor 1
    if ([Convert]::ToHexString($hmac.ComputeHash($signed)) -ceq [Convert]::ToHexString($tag)) { throw 'mutation not rejected' }
} finally { $hmac.Dispose() }
[ordered]@{ checks = @('AES-128 primitive', 'DAT padding roundtrip', 'emoticon IV=key roundtrip', 'synthetic SQLCipher page HMAC/decrypt', 'tampered ciphertext rejected'); passed = $true; limits = 'No real WeChat sample; no WAL or SNS engine execution' } | ConvertTo-Json

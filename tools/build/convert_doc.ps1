# Convert the earlier texts (.cache/olddoc/*.doc) with Microsoft Word into the same "Word filtered HTML" the site
# serves for current texts, plus Word's own plain text of the document body and footnotes (for the independent word
# check). Output: .cache/oldhtml/<name>.htm (UTF-8), <name>.content.txt, <name>.footnotes.txt, or <name>.fail.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/turkey-law/convert_doc.ps1
#
# One invisible Word instance (macros disabled, alerts off), restarted every 40 documents; Word is always quit
# through COM, never killed. Resumable: finished documents are skipped.
param([int]$Limit = 0, [switch]$Reverse)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$src = Join-Path $here '.cache\olddoc'
$dst = Join-Path $here '.cache\oldhtml'
New-Item -ItemType Directory -Force $dst | Out-Null
$utf8 = [Text.UTF8Encoding]::new($false)
$docs = Get-ChildItem $src -Filter *.doc | Sort-Object Name -Descending:$Reverse

function Start-Word {
    $w = New-Object -ComObject Word.Application
    $w.Visible = $false
    $w.DisplayAlerts = 0
    $w.AutomationSecurity = 3   # msoAutomationSecurityForceDisable
    return $w
}

$w = $null
$n = 0
try {
    foreach ($f in $docs) {
        $base = [IO.Path]::GetFileNameWithoutExtension($f.Name)
        $htm = Join-Path $dst "$base.htm"
        $fail = Join-Path $dst "$base.fail"
        if ((Test-Path $htm) -or (Test-Path $fail) -or (Test-Path "$htm.part")) { continue }
        if ($Limit -gt 0 -and $n -ge $Limit) { break }
        if ($null -eq $w -or ($n -gt 0 -and $n % 40 -eq 0)) {
            if ($null -ne $w) { $w.Quit([ref]0); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($w); $w = $null; [GC]::Collect() }
            $w = Start-Word
        }
        $n++
        $d = $null
        try {
            $d = $w.Documents.Open($f.FullName, $false, $true, $false)
            $d.WebOptions.Encoding = 65001   # msoEncodingUTF8
            $tmp = "$htm.part"
            $d.SaveAs2($tmp, 10)             # wdFormatFilteredHTML
            $d.ConvertNumbersToText()        # list labels Word generates are text in the HTML, so make them text here too
            $content = $d.Content.Text
            $notes = ''
            if ($d.Footnotes.Count -gt 0) { $notes = $d.StoryRanges.Item(2).Text }
            $d.Close([ref]0)
            $d = $null
            [IO.File]::WriteAllText((Join-Path $dst "$base.content.txt"), $content, $utf8)
            [IO.File]::WriteAllText((Join-Path $dst "$base.footnotes.txt"), $notes, $utf8)
            Move-Item -Force $tmp $htm
            Write-Output "ok $($f.Name)"
        } catch {
            [IO.File]::WriteAllText($fail, "$($_.Exception.Message)`n", $utf8)
            Write-Output "FAIL $($f.Name): $($_.Exception.Message)"
            if ($null -ne $d) { try { $d.Close([ref]0) } catch {} }
            # Word may have died (RPC server unavailable): start a fresh instance for the next file
            try { $w.Quit([ref]0) } catch {}
            try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($w) } catch {}
            $w = Start-Word
        }
    }
} finally {
    if ($null -ne $w) { $w.Quit([ref]0); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($w) }
}
Write-Output "done: $n converted this run"

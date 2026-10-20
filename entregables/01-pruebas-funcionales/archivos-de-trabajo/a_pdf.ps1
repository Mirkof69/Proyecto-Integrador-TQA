# Convierte un .docx a PDF con Microsoft Word (mismo resultado que «Guardar como PDF»).
#   powershell -ExecutionPolicy Bypass -File a_pdf.ps1 entrada.docx salida.pdf
param([string]$Entrada, [string]$Salida)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open((Resolve-Path $Entrada).Path, $false, $true)
    # Actualiza campos (índice) antes de exportar
    $doc.Fields.Update() | Out-Null
    foreach ($t in $doc.TablesOfContents) { $t.Update() | Out-Null }
    $doc.SaveAs([ref]([System.IO.Path]::GetFullPath($Salida)), [ref]17)  # 17 = wdFormatPDF
    $doc.Close([ref]0)
}
finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}

param(
  [Parameter(Mandatory=$true)]
  [string]$ReportDate,

  [Parameter(Mandatory=$true)]
  [string]$VisualReportDir
)

$ErrorActionPreference = "Stop"

$siteRoot = Split-Path -Parent $PSScriptRoot
$target = Join-Path $siteRoot "reports\$ReportDate"
New-Item -ItemType Directory -Force -Path $target | Out-Null

Copy-Item -LiteralPath (Join-Path $VisualReportDir "fastmoss-56-video-visual-report-$ReportDate.html") -Destination (Join-Path $target "index.html") -Force
Copy-Item -LiteralPath (Join-Path $VisualReportDir "fastmoss-56-video-visual-report-data-$ReportDate.csv") -Destination (Join-Path $target "data.csv") -Force
Copy-Item -LiteralPath (Join-Path $VisualReportDir "visual-report-manifest.json") -Destination (Join-Path $target "visual-report-manifest.json") -Force

$assetSource = Join-Path $VisualReportDir "assets"
$assetTarget = Join-Path $target "assets"
if (Test-Path -LiteralPath $assetTarget) {
  Remove-Item -LiteralPath $assetTarget -Recurse -Force
}
Copy-Item -LiteralPath $assetSource -Destination $assetTarget -Recurse -Force

$firstFrame = Get-ChildItem -LiteralPath (Join-Path $assetTarget "video-first-frames") -File |
  Sort-Object Name |
  Select-Object -First 1
if (-not $firstFrame) {
  throw "No first-frame image found in $assetTarget"
}
$thumbnail = "reports/$ReportDate/assets/video-first-frames/$($firstFrame.Name)"

$reportsJson = Join-Path $siteRoot "reports.json"
$data = Get-Content -LiteralPath $reportsJson -Raw | ConvertFrom-Json
$existing = @($data.reports | Where-Object { $_.date -ne $ReportDate })
$record = [pscustomobject]@{
  date = $ReportDate
  title = "FastMoss 本周四店 56 条可复刻视频报告"
  path = "reports/$ReportDate/"
  items = 56
  stores = 4
  thumbnail = $thumbnail
  notes = "无商品库匹配版，适合选题和视频复刻参考。"
}
$data.updated_at = (Get-Date -Format "yyyy-MM-dd")
$data.reports = @($record) + $existing
$data | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportsJson -Encoding UTF8

Write-Host "Updated site report: $target"

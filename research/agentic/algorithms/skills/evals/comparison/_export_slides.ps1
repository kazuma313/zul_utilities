
param([string]$Pptx, [string]$OutDir, [int]$Width = 640)
$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open($Pptx, $true, $false, $false)
$height = [int]($Width * $pres.PageSetup.SlideHeight / $pres.PageSetup.SlideWidth)
$i = 0
foreach ($slide in $pres.Slides) { $i++; $slide.Export((Join-Path $OutDir ("slide{0:D2}.png" -f $i)), "PNG", $Width, $height) }
$pres.Close()
$app.Quit()

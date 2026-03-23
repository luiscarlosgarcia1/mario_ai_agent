if (Test-Path "obs_test_output") {
    Get-ChildItem "obs_test_output" -Force | Remove-Item -Recurse -Force
    Write-Host "Cleared obs_test_output"
} else {
    Write-Host "obs_test_output does not exist"
}

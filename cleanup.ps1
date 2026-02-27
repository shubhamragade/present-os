$files = @(
    "agent_test_report.json",
    "benchmark_final_results.txt",
    "benchmark_results.txt",
    "debug_output.txt",
    "debug_output_2.txt",
    "debug_output_3.txt",
    "debug_output_4.txt",
    "debug_output_5.txt",
    "e2e_test_final_report.txt",
    "e2e_test_fixed.txt",
    "e2e_test_output.txt",
    "e2e_test_success.txt",
    "integration_log.txt",
    "integration_results.txt",
    "integration_results_final.txt",
    "integration_results_final_2.txt",
    "integration_results_safe.txt",
    "integration_results_verified.txt",
    "server.log",
    "status_response.json",
    "status_response_fixed.json",
    "targeted_agents_report.txt",
    "targeted_agents_report_final.txt",
    "telegram.log",
    "test_browse_traceback.txt",
    "test_browse_traceback_2.txt",
    "test_fireflies_debug.txt",
    "test_fireflies_debug_2.txt",
    "test_learning_debug.txt",
    "test_output.txt",
    "test_results.json",
    "test_results.txt",
    "test_results_final.txt",
    "test_run_repro.txt",
    "test_v2_attempt2.txt",
    "test_v2_traceback.txt",
    "uvicorn.log",
    "voice_test.mp3",
    "voice_test_debug.txt",
    "voice_test_debug_2.txt"
)

Write-Host "Deleting test files..."
foreach ($file in $files) {
    if (Test-Path $file) {
        Remove-Item -Path $file -Force
        Write-Host "Deleted $file"
    }
}

Write-Host "`nStaging changes..."
git add .

Write-Host "`nCommitting changes..."
git commit -m "chore: remove test output and debug files, update README"

Write-Host "`nPushing to GitHub..."
git push

Write-Host "`nDone!"

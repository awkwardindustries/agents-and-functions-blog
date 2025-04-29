$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\src\functions\local.settings.json")) {

    $output = azd env get-values

    # Parse the output to get the endpoint values
    foreach ($line in $output) {
        if ($line -match "AZURE_AI_PROJECT_CONNECTION_STRING"){
            $AIProjectConnectionString = ($line -split "=")[1] -replace '"',''
        }
        if ($line -match "STORAGE_QUEUES_CONNECTION__queueServiceUri"){
            $StorageConnectionQueue = ($line -split "=")[1] -replace '"',''
        }
    }

    @{
        "IsEncrypted" = "false";
        "Values" = @{
            "AzureWebJobsStorage" = "UseDevelopmentStorage=true";
            "FUNCTIONS_WORKER_RUNTIME" = "python";
            "AZURE_AI_PROJECT_CONNECTION_STRING" = "$AIProjectConnectionString";
            "STORAGE_QUEUES_CONNECTION__queueServiceUri" = "$StorageConnectionQueue";
        }
    } | ConvertTo-Json | Out-File -FilePath ".\src\functions\local.settings.json" -Encoding ascii
}
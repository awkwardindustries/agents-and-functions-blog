# agents-and-functions-blog

An end-to-end sample showing an Azure AI Agent Service invoking Azure Functions. This example repository was used in support of the Awkward Industries blog (<https://blog.awkward.industries>) for the post [***Empower Your AI Agents: Harnessing Azure Functions with Azure AI Foundry***]().

## Run Functions Locally

0. Prerequisites:
   1. Install and run [Azurite](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite?tabs=visual-studio%2Cblob-storage#install-azurite)
   2. Python 3.11
   3. Create a virtual environment, `.venv` at the function app root (*src/functions/*):
      ```bash
      cd src/functions
      python -m venv .venv
      source .venv/bin/activate
      pip install -r requirements.txt
      ```
    4. Install the [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
1. Create a `local.settings.json` at the function app root (*src/functions/*) with the following:
   ```json
   {
      "IsEncrypted": "false",
      "Values": {
         "AZURE_AI_PROJECT_CONNECTION_STRING": "$AIProjectConnectionString",
         "AzureWebJobsStorage": "UseDevelopmentStorage=true",
         "FUNCTIONS_WORKER_RUNTIME": "python",
         "STORAGE_QUEUES_CONNECTION__serviceUri": "https://127.0.0.1:10001/devstoreaccount1",
         "STORAGE_QUEUES_CONNECTION__queueServiceUri": "https://127.0.0.1:10001/devstoreaccount1"
      }
   }
   ```

## Deploy to Azure

0. Prerequisites:
   1. Install the [Azure Developer CLI](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd?tabs=winget-windows%2Cbrew-mac%2Cscript-linux&pivots=os-linux)
1. Run `azd up`
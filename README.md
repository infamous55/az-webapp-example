# Azure Web App Example

This repository contains a simple web application written in Python and instructions on how to run it locally or deploy it to Azure.

## Overview

The application is a REST API made using [Python 3.8.10](https://www.python.org/downloads/release/python-3810/) and [FastAPI](https://fastapi.tiangolo.com/). It can perform **C**reate, **R**ead, **U**pdate, and **D**elete operations on blobs within an [Azure Storage Account](https://learn.microsoft.com/en-us/azure/storage/common/storage-account-overview).

Keep in mind that this is for _learning purposes only_. The application doesn't have an authentication and authorization mechanism and doesn't validate the files, so it is **NOT** secure.

If you'd like to learn more about the Azure SDK for Python, read the commented code or refer to the [official documentation](https://learn.microsoft.com/en-us/azure/developer/python/).

## Running locally

First, you need to clone the repository.

```bash
git clone https://github.com/infamous55/az-webapp-example.git && cd az-webapp-example
```

Then, create a virtual environment, activate it, and install the project dependencies.

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

Before you continue, you have to be logged in with Azure CLI, have an Azure Storage Account, and have the _Storage Blob Data Contributor_ role set at the scope of that Storage Account for the application to run properly. If you don't, follow these steps:

1. Sign in with Azure CLI.

```bash
az login
```

2. Create a new resource group.

```bash
az group create --name "<resourcegroupname>" --location "<location>"
```

Note: To list all the available locations, you can use `az account list-locations -o table`. Pick a location that's closer to you.

3. Create a Storage Account.

```bash
az storage account create \
  --name "<storageaccountname>" \
  --resource-group "<resourcegroupname>" \
  --sku "Standard_LRS"
```

4. Save the Storage Account ID (without quotation marks).

```bash
storageaccountid=$( \
  az storage account show \
    --resource-group "<resourcegroupname>" \
    --name "<storageaccountname>" \
    --query "id" \
  | sed -e 's/^"//' -e 's/"$//' \
)
```

5. Save your user ID (without quotation marks).

```bash
userid=$(az ad signed-in-user show --query "userPrincipalName" | sed -e 's/^"//' -e 's/"$//')
```

6. Create a role-assignment.

```bash
az role assignment create \
  --assignee $userid \
  --role "Storage Blob Data Contributor" \
  --scope $storageaccountid
```

Now, rename the `.env.example` file to `.env` and open it using your preferred text editor. Modify the environment variables by replacing the names of your Storage Account and the container that will be created to store all the files.

```bash
mv .env.example .env
```

To start the application, run the following command.

```bash
uvicorn main:app --reload
```

Access at [http://localhost:8000/docs](http://localhost:8000/docs).

## Deploying to Azure

After you run the application locally, you can get it working on Azure by following the next steps.

1. Deploy it to Azure Web App.

```bash
az webapp up \
  --name "<appname>" \
  --resource-group "<resourcegroupname>" \
  --location "<location>" \
  --runtime "PYTHON:3.8" \
  --sku "B1"
```

2. Set the environment variables.

```bash
az webapp config appsettings set \
  --resource-group "<resourcegroupname>" \
  --name "<appname>" \
  --settings STORAGE_ACCOUNT_URL="https://<storageaccountname>.blob.core.windows.net"
```

```bash
az webapp config appsettings set \
  --resource-group "<resourcegroupname>" \
  --name "<appname>" \
  --settings CONTAINER_NAME="<containername>"
```

3. Set the startup file.

```bash
az webapp config set \
  --resource-group "<resourcegroupname>" \
  --name "<appname>" \
  --startup-file "startup.sh"
```

4. Create a Managed Identity for your application.

```bash
az webapp identity assign \
  --resource-group "<resourcegroupname>" \
  --name "<appname>"
```

5. Save the Managed Identity to a variable (without quotation marks).

```bash
webappid=$( \
  az webapp identity show \
    --resource-group "<resourcegroupname>" \
    --name "<appname>" \
    --query "principalId" \
  | sed -e 's/^"//' -e 's/"$//' \
)
```

6. Create a role-assignment.

```bash
az role assignment create \
  --assignee $webappid \
  --resource-group "<resourcegroupname>" \
  --role "Storage Blob Data Contributor"
```

The code also contains a workflow for CI/CD using GitHub Actions. You can enable this from the Deployment Center in the Azure Portal. Make sure to change the `app-name` property to the name of your Azure Web App. Commit and push your project to a GitHub repository for the workflow to execute.

## Cleaning up

To clean up, delete the resource group that you used.

```bash
az group delete --name "<resourcegroupname>"
```

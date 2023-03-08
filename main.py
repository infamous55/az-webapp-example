from fastapi import FastAPI, UploadFile, Path, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.core.exceptions import ResourceNotFoundError
from dotenv import load_dotenv
from os import environ

load_dotenv()

app = FastAPI(
    title="Azure Blobs API Example",
    redoc_url=None
)

# Authorization based on a storage account connection string:
# blob_service_client = BlobServiceClient.from_connection_string(conn_str=environ["STORAGE_ACCOUNT_CONNECTION_STRING"])

# Authorization based on a storage account access key:
# blob_service_client = BlobServiceClient(environ["STORAGE_ACCOUNT_URL"], credential=environ["STORAGE_ACCOUNT_ACCESS_KEY"])

# DefaultAzureCredential relies on "az login" for local development and Managed Identities when the application is deployed to the cloud.
default_credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(environ["STORAGE_ACCOUNT_URL"], credential=default_credential)

# Creating the ContainerClient using DefaultAzureCredential:
container_name = environ["CONTAINER_NAME"]
container_client = ContainerClient(account_url=blob_service_client.url, container_name=container_name, credential=default_credential)

if not container_client.exists():
    container_client.create_container()

# Creating the ContainerClient using a connection string:
# container_client = ContainerClient.from_connection_string(conn_str=environ["CONTAINER_CONNECTION_STRING"], container_name=container_name)
# container_client.create_container()

# Creating a new container with a unique name when the application starts:
# import uuid
# container_name = str(uuid.uuid4())
# container_client = blob_service_client.create_container(container_name, public_access="blob")

class UploadResponse(BaseModel):
    message: str

@app.post("/upload", status_code=status.HTTP_201_CREATED, response_model=UploadResponse, tags=["files"])
def upload_file(file: UploadFile):
    file_contents = file.file.read()
    # Upload using the container client:
    container_client.upload_blob(name=file.filename, data=file_contents, length=file.size)
    # Upload using a blob client:
    # blob_client = blob_service_client.get_blob_client(container=container_name, blob=file.filename)
    # blob_client.upload_blob(data=file_contents, length=file.size)
    return {"message": f"Successfully uploaded {file.filename}"}

class ListFilesResponse(BaseModel):
    files: List[str]

@app.get("/files", response_model=ListFilesResponse, tags=["files"])
def list_all_files():
    blob_list = []
    for blob in container_client.list_blob_names():
        blob_list.append(blob)
    return {"files": blob_list}

@app.get("/files/{filename}", response_class=StreamingResponse, tags=["files"])
def download_file(filename: str = Path()):
    try:
        # Download using the container client:
        blob = container_client.download_blob(blob=filename)
        # Download using a blob client:
        # blob_client = blob_service_client.get_blob_client(container=container_name, blob=filename)
        # blob = blob_client.download_blob()
        return StreamingResponse(blob.chunks())
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
@app.put("/files/{filename}", response_model=UploadResponse, tags=["files"])
def update_file(file: UploadFile, filename: str = Path()):
    blob_client = container_client.get_blob_client(blob=filename)
    if not blob_client.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    # Overwrite using the container client:
    file_contents = file.file.read()
    # container_client.upload_blob(name=file.filename, data=file_contents, length=file.size, overwrite=True)
    # Overwrite using the blob client
    blob_client.upload_blob(data=file_contents, length=file.size, overwrite=True)
    return {"message": f"Successfully updated {filename}"}
    
@app.delete("/files/{filename}", status_code=status.HTTP_204_NO_CONTENT, tags=["files"])
def delete_file(filename: str = Path()):
    try:
        # Delete using the container client:
        container_client.delete_blob(blob=filename)
        # Delete using a blob client:
        # blob_client = blob_service_client.get_blob_client(container=container_name, blob=filename)
        # blob_client.delete_blob()
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
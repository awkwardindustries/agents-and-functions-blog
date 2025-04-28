import azure.functions as func
import json
import logging
import os
import random

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

app = func.FunctionApp()

STORAGE_QUEUE_MESSAGE_ENCODING = "utf-8"

STORAGE_QUEUES_CONNECTION = "STORAGE_QUEUES_CONNECTION"
LIST_INPUT_QUEUE_NAME = "list-projects-request"
LIST_OUTPUT_QUEUE_NAME = "list-projects-response"
STATUS_INPUT_QUEUE_NAME = "project-status-request"
STATUS_OUTPUT_QUEUE_NAME = "project-status-response"

PROJECTS = ["Widget Wonderland", "Gizmo Galaxy", "Wacky Widget Workshop", "Widget Factory Fiesta", "Widget Whirlwind"]
STATUSES = ["Active", "Completed", "Cancelled", "On Hold"]


@app.function_name(name="ListProjects")
@app.queue_trigger(
    arg_name="request", 
    queue_name=LIST_INPUT_QUEUE_NAME, 
    connection=STORAGE_QUEUES_CONNECTION)
@app.queue_output(
    arg_name="response", 
    queue_name=LIST_OUTPUT_QUEUE_NAME, 
    connection=STORAGE_QUEUES_CONNECTION)
def list_projects(
    request: func.QueueMessage, 
    response: func.Out[str]) -> None:
    """
    Azure Function implementation to get the list of all valid
    projects. It is triggered by a Storage Queue message being
    available, and it returns nothing but sends a Storage Queue
    message with the result.

    Parameters:
    request (func.QueueMessage): Input message triggering the
    function for processing
    response (func.Out[str]): Output message including the
    reponse from the function execution

    Returns: None
    """
    logging.info(f"Function list_projects triggered. Message received on queue: {LIST_INPUT_QUEUE_NAME}")

    message_payload = json.loads(request.get_body().decode(STORAGE_QUEUE_MESSAGE_ENCODING))
    logging.info(f"Request message decoded: {message_payload}.")

    correlation_id = message_payload["CorrelationId"]

    result = {
        "Value": {
            "Projects": PROJECTS,
        },
        "CorrelationId": correlation_id,
    }

    # Message formatted for a Storage Queue -- string with UTF-8 encoding
    result_message = json.dumps(result_message).encode(STORAGE_QUEUE_MESSAGE_ENCODING)
    response.set(result_message)
    logging.info(f"Sending response to queue: {LIST_OUTPUT_QUEUE_NAME}. Message: {result}")
    
    logging.info(f"Function list_projects exiting.")


@app.function_name(name="GetProjectStatus")
@app.queue_trigger(
    arg_name="request", 
    queue_name=STATUS_INPUT_QUEUE_NAME, 
    connection=STORAGE_QUEUES_CONNECTION)
@app.queue_output(
    arg_name="response", 
    queue_name=STATUS_OUTPUT_QUEUE_NAME, 
    connection=STORAGE_QUEUES_CONNECTION)
def get_project_status(
    request: func.QueueMessage, 
    response: func.Out[str]) -> None:
    """
    Azure Function implementation to get the current status of the
    given project. It is triggered by a Storage Queue message being
    available, and it returns nothing but sends a Storage Queue
    message with the result.

    Parameters:
    request (func.QueueMessage): Input message triggering the
    function for processing
    response (func.Out[str]): Output message including the
    reponse from the function execution

    Returns: None
    """
    logging.info(f"Function get_project_status triggered. Message received on queue: {STATUS_INPUT_QUEUE_NAME}")

    message_payload = json.loads(request.get_body().decode(STORAGE_QUEUE_MESSAGE_ENCODING))
    logging.info(f"Request message decoded: {message_payload}.")

    project_name = message_payload["Project"]
    correlation_id = message_payload["CorrelationId"]

    logging.info(f"Querying status for project: {project_name}.")
    # Hardcoded as an example
    if project_name in PROJECTS:
        current_status = random.choice(STATUSES)
    else:
        current_status = "Unrecognized Project"

    result = {
        "Value": {
            "Project": project_name,
            "Status": current_status,
        },
        "CorrelationId": correlation_id,
    }

    # Message formatted for a Storage Queue -- string with UTF-8 encoding
    result_message = json.dumps(result_message).encode(STORAGE_QUEUE_MESSAGE_ENCODING)
    response.set(result_message)
    logging.info(f"Sending response to queue: {STATUS_OUTPUT_QUEUE_NAME}. Message: {result}")
    
    logging.info(f"Function get_project_status exiting.")


@app.route(route="CreateAgentAndRun", auth_level=func.AuthLevel.FUNCTION)
def create_agent_and_run(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function implementation that creates an agent, thread, and
    run with the provided prompt. It is triggered by HTTP, and the
    body should include the prompt (e.g., '{ "Prompt": "What's the
    status of the Widget Wonderland project?" }').

    Parameters:
    request (func.HttpRequest): HTTP request including a 'Prompt' in
    the JSON body

    Returns:
    func.HttpResponse: HTTP response with 200 status upon successful
    creation, run, and cleanup of the Agent and a JSON body including
    the last message from the Agent
    """
    logging.info(f"Function create_agent_and_run triggered.")

    logging.info("Checking required input and configuration...")
    project_connection_string = os.environ["AZURE_AI_PROJECT_CONNECTION_STRING"]
    storage_queues_uri = os.environ[f"{STORAGE_QUEUES_CONNECTION}__queueServiceUri"]
    # Azure AI Projects will by default create a 'gpt-4o-mini' model deployment
    # at the time this demo was created. It can be changed by setting an
    # environment variable "AZURE_AI_MODEL_DEPLOYMENT_NAME" as needed.
    model_deployment_name = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o-mini")
    request_body = req.get_json()
    prompt = request_body.get("Prompt")
    if not prompt:
        raise ValueError("Prompt required")

    logging.info("Setting up AI Project Client...")
    project_client = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(),
        conn_str=project_connection_string
    )

    logging.info("Creating an agent with Azure Function tools...")
    agent = project_client.agents.create_agent(
        headers={"x-ms-enable-preview": "true"},
        model=model_deployment_name,
        name="function-created-agent-project-manager",
        instructions="""
            You are a helpful agent who answers questions about projects for
            the Widgets and Things Company. Answer the user's questions to
            the best of your ability. Do not make up answers without having
            data to support your answer.
            """,
        tools=[
            {
                "type": "azure_function",
                "azure_function": {
                    "function": {
                        "name": "GetProjectStatus",
                        "description": "Retrieves the current status of the project.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "Project": {
                                    "type": "string", 
                                    "description": ""
                                },
                                "required": ["Project"]
                            }
                        }
                    },
                    "input_binding": {
                        "type": "storage_queue",
                        "storage_queue": {
                            "queue_service_uri": storage_queues_uri,
                            "queue_name": STATUS_INPUT_QUEUE_NAME
                        }
                    },
                    "output_binding": {
                        "type": "storage_queue",
                        "storage_queue": {
                            "queue_service_uri": storage_queues_uri,
                            "queue_name": STATUS_OUTPUT_QUEUE_NAME
                        }
                    }
                }
            },
            {
                "type": "azure_function",
                "azure_function": {
                    "function": {
                        "name": "ListProjects",
                        "description": "Retrieves the current list of projects."
                    },
                    "input_binding": {
                        "type": "storage_queue",
                        "storage_queue": {
                            "queue_service_uri": storage_queues_uri,
                            "queue_name": LIST_INPUT_QUEUE_NAME
                        }
                    },
                    "output_binding": {
                        "type": "storage_queue",
                        "storage_queue": {
                            "queue_service_uri": storage_queues_uri,
                            "queue_name": LIST_OUTPUT_QUEUE_NAME
                        }
                    }
                }
            }
        ]
    )
    logging.info(f"Agent created, agent ID: {agent.id}")

    logging.info("Creating a thread...")
    thread = project_client.agents.create_thread()
    logging.info(f"Thread created, thread ID: {thread.id}")

    logging.info("Adding prompt to the thread...")
    user_message = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=prompt,
    )
    logging.info(f"User message created, message ID: {user_message.id}")

    logging.info("Running the thread...")
    run = project_client.agents.create_and_process_run(
        thread_id=thread.id,
        agent_id=agent.id
    )
    logging.info(f"Run finished with status: {run.status}")

    if run.status == "failed":
        return logging.error(f"Run failed: {run.last_error}")
    
    run_messages = project_client.agents.list_messages(thread_id=thread.id)
    logging.info(f"Messages: {run_messages.data}")
    
    logging.info("Cleaning up agent...")
    project_client.agents.delete_agent(agent_id=agent.id)
    logging.info("Agent deleted.")

    return func.HttpResponse(
        body=json.dumps(run_messages.data),
        mimetype="application/json",
        status_code=200)
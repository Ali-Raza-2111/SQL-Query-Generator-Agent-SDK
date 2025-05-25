import os
from dotenv import load_dotenv
import chainlit as cl
from agents import Agent, Runner, OpenAIChatCompletionsModel, function_tool
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Get Gemini API key from environment
gemini_api_key = os.getenv('GOOGLE_API_KEY')

# Initialize OpenAI client for Gemini endpoint
client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url='https://generativelanguage.googleapis.com/v1beta/openai/'
)

# Function tool to write a query string into a newsql.sql file
@function_tool
def write_query_to_sql_file(query: str, filename: str) -> dict:
    """
    Writes a given SQL query string into a specified file inside 'SQL Queries' folder.
    
    Parameters:
    - query (str): The SQL query to be written.
    - filename (str): The name of the file (with or without .sql extension) to store the query.
    
    Returns:
    - A dictionary with a message confirming the action.
    """
    try:
        # Ensure the 'SQL Queries' folder exists
        os.makedirs("SQL Queries", exist_ok=True)

        # Ensure filename ends with .sql
        if not filename.lower().endswith(".sql"):
            filename += ".sql"

        file_path = os.path.join("SQL Queries", filename)

        # Open the file in append mode and write the query
        with open(file_path, "a") as f:
            f.write(query.strip() + "\n\n")  # Add two line breaks for separation

        return {"message": f"✅ Query successfully written to '{file_path}'."}

    except Exception as e:
        return {"message": f"❌ Failed to write query: {e}"}

# Define your agent with the tool included
agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant. The user gives you the problems and its you task that you write the sql queries of those problems in file given by the user.",
    model=OpenAIChatCompletionsModel(
        model='gemini-2.0-flash',
        openai_client=client
    ),
    tools=[write_query_to_sql_file]  # Attach the tool
)

# Chainlit message handler
@cl.on_message
async def main(message: cl.Message):
    try:
        # Run the agent asynchronously with the user message
        result = await Runner.run(agent, message.content)

        # Send the agent's final response back to Chainlit UI
        await cl.Message(content=result.final_output).send()

    except Exception as e:
        # Gracefully handle and display errors
        await cl.Message(content=f"Error: {str(e)}").send()

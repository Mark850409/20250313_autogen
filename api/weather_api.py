import asyncio
import os
import requests
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API keys from environment variables
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("MODEL")

def get_weather(city: str) -> str:
    """Get weather information for a specified city"""
    if not WEATHER_API_KEY:
        return "Error: WEATHER_API_KEY not found in environment variables"

    api_url = f"https://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        
        weather_text = data['current']['condition']['text']
        temperature = data['current']['temp_c']
        
        return f"Weather in {city}: {weather_text}, Temperature: {temperature}°C"
    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data for {city}: {str(e)}"

async def main() -> None:
    # Initialize Gemini model client
    model_client = OpenAIChatCompletionClient(
        api_key=GEMINI_API_KEY,
        model=MODEL
    )
    
    # Create assistant agent
    agent = AssistantAgent(
        "weather_assistant",
        model_client=model_client
    )
    
    # Get weather for Taipei
    weather_info = get_weather("Taipei")
    
    # Generate response using the agent
    response = await agent.run(
        task=f"Current weather report: {weather_info}"
    )
    print(response)
    
    await model_client.close()

# Handle asyncio event loop
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    if loop.is_running():
        task = loop.create_task(main())
    else:
        asyncio.run(main())

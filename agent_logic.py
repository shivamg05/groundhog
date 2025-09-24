import openai
import os
import base64
from dotenv import load_dotenv
import json
import re

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_next_action(image_path, goal_text, dom_snapshot=None):
    # Encode the image
    with open(image_path, "rb") as img_file:
        base64_image = base64.b64encode(img_file.read()).decode("utf-8")

    # Master prompt with formatting constraint
    prompt = f"""
        You are an expert web automation agent. Based on the provided screenshot and the high-level goal, determine the single next action to take. The available actions are 'click', 'type', and 'finish'. Respond ONLY with a JSON object containing your reasoning and the action.

        High-Level Goal: {goal_text}

        JSON format:
        {{
        "reasoning": "A brief thought process on why you are choosing this action.",
        "action": {{
            "type": "click" | "type" | "finish",
            "selector": "CSS selector for the element, if applicable.",
            "text": "The text to type, if applicable."
        }}
        }}
    """.strip()

    if dom_snapshot:
        dom_json = json.dumps(dom_snapshot, indent=2)
        prompt += f"\n\nVisible Page Snapshot:\n{dom_json}"

    # Call the GPT-4o-mini Vision model
    response = openai.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": "You are an expert web automation agent. Respond only with a valid JSON object as instructed."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        },
                    },
                ],
            },
        ],
        temperature=0.3,
    )

    # Extract and parse JSON response
    try:
        json_response = response.choices[0].message.content.strip()

        if json_response.startswith("```"):
            json_response = re.sub(r"^```(?:json)?\s*|\s*```$", "", json_response.strip())


        print("Model Raw Response:", json_response)
        return json.loads(json_response)
    except Exception as e:
        print("❌ Failed to parse JSON from model:", e)
        return None

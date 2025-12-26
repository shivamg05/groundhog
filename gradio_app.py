import gradio as gr
import sys
import os

# Ensure core modules are found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.browser import Browser
from core.processor import Processor
from core.controller import AgentController
# NOTE: In Colab, we assume user installed requirements. 
# Import ModelEngine inside function to avoid startup lag if not needed immediately.

def run_agent_interactive(goal, url):
    """
    This function drives the Gradio UI.
    """
    # 1. Init (Lazy load to keep UI snappy)
    try:
        from core.model import ModelEngine
        # Check if model is already loaded in global scope to avoid reloading (optional optimization)
        if 'model_engine' not in globals():
            global model_engine
            # If repo_id is provided in config, use that. Otherwise assumes local or standard.
            # For the demo, we assume the user has access to the model via HF or local path.
            # Using your HF repo ID here is best for the Colab demo!
            model_engine = ModelEngine(model_id="shivamg05/groundhog-v1", adapter_path=None)
    except Exception as e:
        yield None, f"❌ Error loading model: {e}"
        return

    browser = Browser(headless=True)
    processor = Processor()
    agent = AgentController(browser, processor, model_engine)

    try:
        # Loop through the generator
        for update in agent.run_task_generator(goal, url):
            # Yield image and log to update UI
            yield update["screenshot"], update["log"]
            
    except Exception as e:
        yield None, f"💥 Error: {e}"
    finally:
        browser.quit()

# --- BUILD UI ---
with gr.Blocks(title="🐹 Groundhog Agent") as demo:
    gr.Markdown("# 🐹 Groundhog: Autonomous Web Agent")
    gr.Markdown("Enter a goal and a URL. The agent will open a headless browser and you can watch it work below.")
    
    with gr.Row():
        goal_input = gr.Textbox(label="Goal", placeholder="Find the contact email for IANA")
        url_input = gr.Textbox(label="Starting URL", value="https://www.iana.org/domains")
    
    run_btn = gr.Button("Run Agent", variant="primary")
    
    with gr.Row():
        # The Live View
        browser_view = gr.Image(label="Live Browser View", type="pil")
        # The Logs
        log_output = gr.Textbox(label="Agent Thought Process", lines=20)

    run_btn.click(
        fn=run_agent_interactive,
        inputs=[goal_input, url_input],
        outputs=[browser_view, log_output]
    )

if __name__ == "__main__":
    # share=True creates a public link usable from Colab
    demo.launch(share=True)
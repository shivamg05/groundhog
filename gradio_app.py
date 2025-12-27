import gradio as gr
import sys
import os
import signal
import gc
import torch

# Ensure core modules are found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.browser import Browser
from core.processor import Processor
from core.controller import AgentController

def shutdown_system():
    """
    Unloads model, clears cache, and kills the Colab/Python process.
    """
    print("Shutting down...")
    if 'model_engine' in globals():
        del globals()['model_engine']
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()
    os.kill(os.getpid(), signal.SIGTERM)

def run_agent_interactive(goal, url):
    """
    This function drives the Gradio UI.
    Yields: (Image, Log, Run_Button_Update, Stop_Button_Update)
    """
    # LOADING
    yield (
        None, 
        "Initializing System...", 
        gr.update(value="Model Loading...", interactive=False), 
        gr.update(interactive=True) 
    )

    # Init Model
    try:
        from core.model import ModelEngine
        if 'model_engine' not in globals():
            global model_engine
            model_engine = ModelEngine(model_id="shivamg05/groundhog-v1", adapter_path=None)
    except Exception as e:
        # Reset buttons on error
        yield (
            None, 
            f"❌ Error loading model: {e}", 
            gr.update(value="Run Agent", interactive=True), 
            gr.update(interactive=False)
        )
        return

    # RUNNING
    yield (
        None, 
        "Model Loaded. Launching Browser...", 
        gr.update(value="Task Running...", interactive=False), 
        gr.update(interactive=True)
    )

    browser = Browser(headless=True)
    processor = Processor()
    agent = AgentController(browser, processor, model_engine)

    try:
        # Loop through generator
        for update in agent.run_task_generator(goal, url):
            yield (
                update["screenshot"], 
                update["log"], 
                gr.update(value="Task Running...", interactive=False), 
                gr.update(interactive=True)
            )
            
    except Exception as e:
        yield (
            None, 
            f"💥 Error: {e}", 
            gr.update(value="Run Agent", interactive=True), 
            gr.update(interactive=False)
        )
    finally:
        browser.quit()
        # FINISHED/STOPPED
        yield (
            None, 
            "Task Process Ended.", 
            gr.update(value="Run Agent", interactive=True), 
            gr.update(interactive=False)
        )

# BUILD UI
with gr.Blocks(title="🦫 Groundhog Agent") as demo:
    gr.Markdown("# 🦫 Groundhog: Autonomous Web Agent")
    
    with gr.Row():
        goal_input = gr.Textbox(label="Goal", placeholder="Find the cheapest laptop and add it to cart", scale=2)
        url_input = gr.Textbox(label="Starting URL", placeholder="https://www.bestbuy.com/home", scale=1)
    
    with gr.Row():
        run_btn = gr.Button("Run Agent", variant="primary", scale=2)
        # Initialize Stop button as DISABLED
        stop_btn = gr.Button("⏹️ Stop Task", variant="stop", scale=1, interactive=False)
    
    with gr.Row():
        browser_view = gr.Image(label="Live Browser View", type="pil")
        log_output = gr.Textbox(label="Agent Thought Process", lines=20, autoscroll=True)

    with gr.Row():
        kill_btn = gr.Button("⚠️ Unload Model & Stop Colab", variant="secondary")

    # EVENTS
    
    # Run Event
    run_event = run_btn.click(
        fn=run_agent_interactive,
        inputs=[goal_input, url_input],
        outputs=[browser_view, log_output, run_btn, stop_btn]
    )

    # Stop Task Event
    stop_btn.click(
        fn=None,
        inputs=None,
        outputs=None,
        cancels=[run_event]
    )

    # Kill Event
    kill_btn.click(
        fn=shutdown_system,
        inputs=None,
        outputs=None
    )

if __name__ == "__main__":
    demo.launch(share=True)
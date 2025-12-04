import argparse
import sys
import os
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from core.browser import Browser
from core.processor import Processor
from core.controller import AgentController

def main():
    # 1. Parse Arguments
    parser = argparse.ArgumentParser(description="Groundhog: Autonomous Web Agent")
    parser.add_argument("--goal", type=str, required=True, help="The natural language task you want to achieve")
    parser.add_argument("--url", type=str, required=True, help="The starting URL")
    parser.add_argument("--steps", type=int, default=15, help="Max steps to execute")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode (no visible window)")
    
    args = parser.parse_args()

    print(f"\n🐹 Initializing Groundhog Agent...")
    print(f"   Goal: {args.goal}")
    print(f"   URL:  {args.url}")
    
    browser = None

    try:
        # 2. Init Body (Browser)
        print("   [1/3] Launching Browser...")
        browser = Browser(headless=args.headless)

        # 3. Init Eyes (Processor)
        print("   [2/3] Initializing Processor...")
        processor = Processor()
        
        # 4. Init Brain (Model)
        # NOTE: This requires CUDA/NVIDIA GPU for the 4-bit config in core/model.py
        print("   [3/3] Loading Model (this will take a moment)...")
        try:
            from core.model import ModelEngine
            model = ModelEngine() 
        except Exception as e:
            print(f"\n❌ CRITICAL MODEL ERROR: {e}")
            print("   -> If you are on a Mac, 4-bit quantization (BitsAndBytes) is not supported.")
            print("   -> Please deploy to a Linux GPU server (RunPod, Colab, etc) to run the full agent.")
            return

        # 5. Init Controller
        agent = AgentController(browser, processor, model)

        # 6. Run the Loop
        start_time = time.time()
        success = agent.run_task(args.goal, args.url, args.steps)
        duration = time.time() - start_time

        if success:
            print(f"\n✨ Task Completed Successfully in {duration:.2f}s!")
        else:
            print(f"\n💀 Task Failed or Hit Max Steps ({duration:.2f}s).")
            
    except KeyboardInterrupt:
        print("\n\n🛑 User stopped execution.")
    except Exception as e:
        print(f"\n💥 Unexpected Runtime Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if browser:
            print("🔒 Closing browser...")
            browser.quit()

if __name__ == "__main__":
    main()
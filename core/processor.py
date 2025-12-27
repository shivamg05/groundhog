import re
from bs4 import BeautifulSoup
from PIL import Image

class Processor:
    def __init__(self, max_elements=200):
        self.max_elements = max_elements
        self.TARGET_WIDTH = 1024
        self.MAX_HEIGHT = 1280

    def clean_text(self, text, max_len=60):
        """Truncate text to save tokens, but keep enough to be readable."""
        if not text:
            return ""
        # Remove tags-like strings
        text = re.sub(r'<[^>]+>', '', text)
        # Collapse multiple spaces
        text = " ".join(text.split())
        return text[:max_len]

    def format_attributes(self, attrs):
        """Format attributes, filtering out defaults to save tokens."""
        out = []

        # Type Attribute (Strip defaults)
        if "type" in attrs:
            t = attrs["type"].lower().strip()
            if t not in ["text", "button", "reset"]:
                out.append(f"type='{t}'")

        # Key Attributes for Accessibility/Identification
        target_attrs = ["role", "name", "value", "aria-label", "placeholder", "title", "alt"]
        for k in target_attrs:
            if k in attrs and attrs[k]:
                val = self.clean_text(str(attrs[k]), 40)
                if val:
                    # Shorten key names for compactness
                    key_map = {"aria-label": "aria", "placeholder": "ph"}
                    nice_key = key_map.get(k, k)
                    out.append(f"{nice_key}='{val}'")

        # State Attributes
        for k in ["checked", "disabled", "selected", "required", "readonly"]:
            if k in attrs:
                out.append(k)

        return "(" + ", ".join(out) + ")" if out else ""

    def distill_dom(self, html_string):
        """
        Parses raw HTML and returns a compact, token-efficient string representation.
        ONLY includes elements that are currently visible in the viewport.
        CRITICAL: Matches the format used in training (groundhog-data-processing.ipynb).
        """
        soup = BeautifulSoup(html_string, "html.parser")

        # prune structural junk
        for tag in soup.find_all(["script", "style", "meta", "link", "noscript", "svg", "path", "footer", "head"]):
            tag.decompose()

        # start with the sentinel token
        candidates = [
            "[0] <option> Target element is not in this list"
        ]

        # Define what we keep (Copied from training logic)
        INTERACTIVE_TAGS = {"a", "button", "input", "select", "textarea", "option", "label", "li", "summary"}
        INTERACTIVE_ROLES = {"button", "tab", "link", "checkbox", "menuitem", "radio", "combobox", "listbox", "option", "switch", "searchbox"}
        HEADER_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

        # traverse ALL tags in document order
        for tag in soup.find_all(True):
            # use our custom injected ID
            uid = tag.attrs.get("data-m2w-id", "")

            is_visible = tag.attrs.get("data-m2w-visible", "false") == "true"

            # condition A: Header (Keep for context, even without ID)
            if tag.name in HEADER_TAGS:
                text = self.clean_text(tag.get_text(separator=" ", strip=True))
                if text:
                    candidates.append(f"[-] <{tag.name}> {text}")
                continue

            # condition B: Must have a UID to be actionable
            if not uid:
                continue

            #condition C: visibility + interactive check
            if not is_visible:
                continue

            is_interactive_tag = tag.name in INTERACTIVE_TAGS
            
            role = tag.attrs.get("role", "")
            if isinstance(role, list): role = role[0]
            is_interactive_role = role in INTERACTIVE_ROLES

            if is_interactive_tag or is_interactive_role:
                text = self.clean_text(tag.get_text(separator=" ", strip=True))
                attr_str = self.format_attributes(tag.attrs)

                #skip empty generic containers unless they are inputs
                if not text and not attr_str and tag.name not in ["input", "button", "select", "textarea"]:
                    continue

                # formatting: [1250] <li> Car (role='tab')
                line = f"[{uid}] <{tag.name}> {text} {attr_str}"
                line = " ".join(line.split())
                candidates.append(line)

        # safety limit
        if len(candidates) > self.max_elements:
            candidates = candidates[:self.max_elements]

        return "\n".join(candidates)
    
    def process_image(self, image):
        """
        Resizes and crops the screenshot exactly as done during training.
        This prevents distribution shift.
        """
        # calculate new height to preserve aspect ratio based on fixed width
        w_percent = (self.TARGET_WIDTH / float(image.size[0]))
        h_size = int((float(image.size[1]) * float(w_percent)))

        # resize the image (High Quality)
        img_resized = image.resize((self.TARGET_WIDTH, h_size), Image.LANCZOS)

        # smart Crop (Viewport Simulation)
        # If the resulting image is too tall, chop off the bottom
        if h_size > self.MAX_HEIGHT:
            img_resized = img_resized.crop((0, 0, self.TARGET_WIDTH, self.MAX_HEIGHT))
            
        return img_resized

    def format_prompt(self, goal, distilled_dom):
        """
        Constructs the exact string prompt expected by the VLM.
        """
        prompt = (
            f"You are a web agent. Analyze the screenshot and the list of elements.\n"
            f"The element list is formatted as: [element_id] <Tag> Text (Attributes).\n"
            f"If the target element is not in the list, select ID 0 to scroll down on the page.\n"
            f"Your task is to select the correct Element ID to perform the chosen action on.\n\n"
            f"TASK: {goal}\n\n"
            f"ELEMENTS:\n{distilled_dom}\n\n"
            f"Generate a JSON with keys: action, element_id, value, is_finished. "
            f"The action chosen can be either 'click', 'type', or 'select'.\n"
            f"IMPORTANT: Set 'is_finished' to true ONLY when the task is fully completed "
            f"and you have reached the final goal state. Do not set it to true after intermediate steps."
        )
        return prompt
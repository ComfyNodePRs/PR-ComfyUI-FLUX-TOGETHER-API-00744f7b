import io
import os
import configparser
from enum import Enum
from urllib.parse import urljoin
from PIL import Image
import numpy as np
import torch
from together import Together
import base64
import json
from tenacity import retry, stop_after_attempt, wait_exponential

class Status(Enum):
    TASK_NOT_FOUND = "Task not found"
    PENDING = "pending"
    REQUEST_MODERATED = "Request Moderated"
    CONTENT_MODERATED = "Content Moderated"
    READY = "completed"
    ERROR = "error"

class ConfigLoader:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        config_path = os.path.join(parent_dir, "config.ini")
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.set_api_key()

    def get_key(self, section, key):
        try:
            return self.config[section][key]
        except KeyError:
            raise KeyError(f"{key} not found in section {section} of config file.")

    def set_api_key(self):
        try:
            api_key = self.get_key('API', 'API_KEY')
            os.environ["TOGETHER_API_KEY"] = api_key
        except KeyError as e:
            print(f"Error: {str(e)}")

config_loader = ConfigLoader()

class BaseFlux:
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate_image"
    CATEGORY = "Together.ai"

    def __init__(self):
        self.client = Together()

    def process_result(self, result):
        try:
            print(f"Debug - Result type: {type(result)}")
            print(f"Debug - Result content: {result}")
            
            if isinstance(result, dict) and 'data' in result:
                img_data = result['data'][0]['b64_json']
            elif hasattr(result, 'data') and hasattr(result.data[0], 'b64_json'):
                img_data = result.data[0].b64_json
            else:
                raise ValueError("Unexpected response format")

            img_bytes = base64.b64decode(img_data)
            img = Image.open(io.BytesIO(img_bytes))
            img_array = np.array(img).astype(np.float32) / 255.0
            img_tensor = torch.from_numpy(img_array)[None,]
            return (img_tensor,)
        except Exception as e:
            print(f"Error processing image result: {str(e)}")
            return self.create_blank_image()

    def create_blank_image(self):
        blank_img = Image.new('RGB', (512, 512), color='black')
        img_array = np.array(blank_img).astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_array)[None,]
        return (img_tensor,)

    def check_multiple_of_32(self, width, height):
        if width % 32 != 0 or height % 32 != 0:
            raise ValueError(f"Width {width} and height {height} must be multiples of 32.")

    def generate_image(self, model_path, arguments):
        self.check_multiple_of_32(arguments["width"], arguments["height"])

        try:
            response = self.client.images.generate(
                model=model_path,
                prompt=arguments["prompt"],
                width=arguments["width"],
                height=arguments["height"],
                steps=arguments["steps"],
                n=1,
                response_format="b64_json",
                **{k: v for k, v in arguments.items() if k not in ["prompt", "width", "height", "steps"]}
            )
            return self.process_result(response)
        except Exception as e:
            print(f"Error generating image: {str(e)}")
            return self.create_blank_image()

class FluxPro11(BaseFlux):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "width": ("INT", {"default": 1024, "min": 256, "max": 1440}),
                "height": ("INT", {"default": 1024, "min": 256, "max": 1440}),
                "prompt_upsampling": ("BOOLEAN", {"default": True}),
                "steps": ("INT", {"default": 1, "min": 1, "max": 1}),
                "safety_tolerance": (["1", "2", "3", "4", "5", "6"], {"default": "2"}),
            },
            "optional": {
                "seed": ("INT", {"default": -1})
            }
        }

    def generate_image(self, prompt, width, height, prompt_upsampling, steps, safety_tolerance, seed=-1):
        arguments = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "prompt_upsampling": prompt_upsampling,
            "steps": steps,
            "safety_tolerance": safety_tolerance
        }
        if seed != -1:
            arguments["seed"] = seed
        return super().generate_image("black-forest-labs/FLUX.1.1-pro", arguments)

class FluxDev(BaseFlux):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "width": ("INT", {"default": 1024, "min": 256, "max": 1440}),
                "height": ("INT", {"default": 1024, "min": 256, "max": 1440}),
                "steps": ("INT", {"default": 4, "min": 1, "max": 4}),
                "prompt_upsampling": ("BOOLEAN", {"default": True}),
                "safety_tolerance": (["1", "2", "3", "4", "5", "6"], {"default": "2"}),
                "guidance": ("FLOAT", {"default": 3.0, "min": 0.1, "max": 10.0}),
            },
            "optional": {
                "seed": ("INT", {"default": -1})
            }
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_image(self, prompt, width, height, steps, prompt_upsampling, safety_tolerance, guidance, seed=-1):
        arguments = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "prompt_upsampling": prompt_upsampling,
            "safety_tolerance": safety_tolerance,
            "guidance_scale": guidance  # Changed from guidance to guidance_scale to match API expectations
        }
        if seed != -1:
            arguments["seed"] = seed
        
        try:
            # Override the base class method to handle the response directly
            self.check_multiple_of_32(width, height)
            response = self.client.images.generate(
                model="black-forest-labs/FLUX.1-schnell-Free",
                prompt=prompt,
                width=width,
                height=height,
                steps=steps,
                n=1,
                response_format="b64_json",
                guidance_scale=guidance,  # Explicitly pass guidance_scale
                seed=seed if seed != -1 else None,
                safety_tolerance=safety_tolerance,
                prompt_upsampling=prompt_upsampling
            )
            return self.process_result(response)
        except Exception as e:
            print(f"Error generating image: {str(e)}")
            return self.create_blank_image()

class FluxPro(BaseFlux):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "width": ("INT", {"default": 1024, "min": 256, "max": 1440}),
                "height": ("INT", {"default": 1024, "min": 256, "max": 1440}),
                "steps": ("INT", {"default": 4, "min": 1, "max": 40}),
                "prompt_upsampling": ("BOOLEAN", {"default": True}),
                "safety_tolerance": (["1", "2", "3", "4", "5", "6"], {"default": "2"}),
                "guidance": ("FLOAT", {"default": 2.5, "min": 0.1, "max": 10.0}),
                "interval": ("INT", {"default": 2, "min": 1, "max": 10}),
            },
            "optional": {
                "seed": ("INT", {"default": -1})
            }
        }

    def generate_image(self, prompt, width, height, steps, prompt_upsampling, safety_tolerance, guidance, interval, seed=-1):
        arguments = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "prompt_upsampling": prompt_upsampling,
            "safety_tolerance": safety_tolerance,
            "guidance": guidance,
            "interval": interval
        }
        if seed != -1:
            arguments["seed"] = seed
        return super().generate_image("black-forest-labs/FLUX.1-pro", arguments)

NODE_CLASS_MAPPINGS = {
    "FluxPro11_TOGETHER": FluxPro11,
    "FluxDev_TOGETHER": FluxDev,
    "FluxPro_TOGETHER": FluxPro
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FluxPro11_TOGETHER": "Flux Pro 1.1 (TOGETHER)",
    "FluxDev_TOGETHER": "Flux Dev (TOGETHER)",
    "FluxPro_TOGETHER": "Flux Pro (TOGETHER)"
}

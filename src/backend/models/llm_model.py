"""
LLM Model Wrapper for Empathetic Chatbot
Using Qwen3-14B for generating empathetic responses
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Dict
import re


class EmpatheticLLM:
    """
    Wrapper for Qwen3 LLM with empathetic conversation capabilities
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-14B",
        system_prompt: str = "",
        max_new_tokens: int = 300,
        
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.2,
        no_repeat_ngram_size: int = 3,
        device: str = None
    ):
        """
        Initialize the empathetic LLM

        Args:
            model_name: HuggingFace model name
            system_prompt: System prompt for guiding the model
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            repetition_penalty: Penalty for repetition
            no_repeat_ngram_size: Size of n-grams to avoid repetition
            device: Device to load model on
        """
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.repetition_penalty = repetition_penalty
        self.no_repeat_ngram_size = no_repeat_ngram_size

        # Determine device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"[LLM] Loading model: {model_name}")
        print(f"[LLM] Using device: {self.device}")

        # Load model and tokenizer
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            dtype=torch.bfloat16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None,
            trust_remote_code=True
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )

        if self.device != "cuda":
            self.model = self.model.to(self.device)

        print(f"[LLM] Model loaded successfully")
        print(f"[LLM] NO local conversation storage - using Vertex AI Memory Bank only")

    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate empathetic response based on provided messages

        NO LOCAL STORAGE - messages should come from Vertex AI Memory Bank

        Args:
            messages: List of conversation messages
                     Format: [{"role": "system/user/assistant", "content": "..."}]

        Returns:
            Generated response text
        """
        if not messages:
            return "안녕하세요! 편하게 이야기 나눠요."

        # Apply chat template
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # Tokenize
        inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
                do_sample=True,
                repetition_penalty=self.repetition_penalty,
                no_repeat_ngram_size=self.no_repeat_ngram_size,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )

        # Decode response
        response = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )

        # Clean response
        clean_response = self._clean_response(response)

        # NO local storage - return response only
        return clean_response

    def _clean_response(self, response: str) -> str:
        """
        Clean the generated response by removing unwanted characters and artifacts

        Args:
            response: Raw generated response

        Returns:
            Cleaned response
        """
        clean = response

        # Remove <think>...</think> blocks (Qwen3 internal reasoning)
        clean = re.sub(r'<think>.*?</think>', '', clean, flags=re.DOTALL)

        # Remove any remaining XML-like tags
        clean = re.sub(r'<[^>]+>', '', clean)

        # Remove content in parentheses
        if '(' in clean:
            clean = clean[:clean.index('(')]

        # Remove arrows and special markers (cut at first occurrence)
        for arrow in ['→', '->', '＞', '※', '■', '□']:
            if arrow in clean:
                clean = clean[:clean.index(arrow)]

        # Strip leading/trailing whitespace
        clean = clean.strip()

        # Fallback if response is too short or empty
        if not clean or len(clean) < 5:
            clean = "죄송해요, 다시 한번 말씀해주시겠어요?"

        return clean

from transformers import AutoProcessor, AutoModelForCausalLM

MODEL_ID = "google/functiongemma-270m-it"

# Load processor & model
processor = AutoProcessor.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    device_map="auto",
    torch_dtype="auto"
)

print("✅ FunctionGemma loaded successfully")

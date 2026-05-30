"""
Registry untuk auto-discovery tool via decorator @register_tool.

File ini dipisahkan dari __init__.py untuk menghindari circular import:
  - Tool files (metadata.py, silence.py, dll) mengimport register_tool dari sini
  - __init__.py mengimport TOOL_REGISTRY dan TOOL_SCHEMAS dari sini setelah semua tool ter-register

Untuk menambah tool baru, cukup:
  1. Buat file tool baru di src/tools/
  2. Dekorasi fungsi utama dengan @register_tool
  3. Import fungsi tersebut di __init__.py

Schema JSON akan otomatis ter-generate dari type hints dan docstring.
"""
import inspect
from typing import Callable, get_type_hints

TOOL_REGISTRY: dict[str, Callable] = {}
TOOL_SCHEMAS: list[dict] = []


def register_tool(func: Callable) -> Callable:
    """
    Decorator untuk mendaftarkan fungsi sebagai tool yang bisa dipanggil LLM.
    
    Cara pakai:
        @register_tool
        def my_tool(file_path: str) -> dict:
            \"\"\"Deskripsi tool yang akan muncul di LLM.\"\"\"
            ...
    
    Decorator ini otomatis:
    1. Menambahkan fungsi ke TOOL_REGISTRY dengan nama fungsi sebagai key.
    2. Membuat JSON schema dari type hints dan docstring, lalu tambahkan ke TOOL_SCHEMAS.
    """
    TOOL_REGISTRY[func.__name__] = func
    
    hints = get_type_hints(func)
    sig = inspect.signature(func)
    
    properties = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        if param_name == "return":
            continue
        
        python_type = hints.get(param_name, str)
        if python_type == str:
            json_type = "string"
        elif python_type == float:
            json_type = "number"
        elif python_type == int:
            json_type = "integer"
        elif python_type == bool:
            json_type = "boolean"
        else:
            json_type = "string"
        
        properties[param_name] = {
            "type": json_type,
            "description": f"Parameter {param_name} untuk {func.__name__}"
        }
        
        if param.default is inspect.Parameter.empty:
            required.append(param_name)
    
    docstring = (func.__doc__ or "").strip()
    description = docstring.split('\n')[0] if docstring else func.__name__
    
    schema = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }
    
    TOOL_SCHEMAS.append(schema)
    return func

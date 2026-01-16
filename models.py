# Copyright (c) 2025 ETH Zurich.
#                    All rights reserved.
#
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# Model loading utilities (reused from MultiAgent-GameTheory)
# Modified to use OpenRouter API

import logging
import os
import sys

# Independent project - load .env from current directory only
current_dir = os.path.dirname(os.path.abspath(__file__))

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

# Load .env from current directory only (independent project)
current_env_path = os.path.join(current_dir, '.env')

if os.path.exists(current_env_path):
    load_dotenv(current_env_path, override=True)
    print(f"✓ Loaded .env from current directory: {current_env_path}")
else:
    # Fallback to system environment variables
    load_dotenv()
    print("⚠️ No .env file found, using system environment variables")

# Set all env vars to have the same name automatically
for k, v in os.environ.items():
    os.environ[k] = v

def get_model_by_id_and_provider(model_id: str, provider: str = None):
    """
    Get a model by ID and provider.
    Uses OpenRouter API if OPENROUTER_API_KEY is set.
    FORCES use of OpenRouter - no fallback to OpenAI.
    
    Args:
        model_id (str): The model ID (e.g., "gpt-4o", "gpt-4o-mini")
        provider (str, optional): The model provider
    
    Returns:
        Model instance
    """
    # Check if OpenRouter API key is available
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    
    # Use OpenRouter if key exists and is valid
    use_openrouter = openrouter_key and openrouter_key.strip() and openrouter_key.startswith("sk-or-v1")
    
    if not use_openrouter:
        raise ValueError(
            f"OPENROUTER_API_KEY is not set or invalid. "
            f"Current value: {openrouter_key[:20] if openrouter_key else 'Not set'}... "
            f"Please set a valid OpenRouter API key (starts with 'sk-or-v1-') in your .env file."
        )
    
    # Debug: Print OpenRouter key prefix
    print(f"🔑 Using OpenRouter key: {openrouter_key[:20]}...")
    
    properties = {
        "temperature": 0,
        "max_retries": 5,  # Increased retries for rate limit handling
        "timeout": 60  # Add timeout
    }
    
    # Force use OpenRouter (no fallback)
    from langchain_openai import ChatOpenAI
    
    # Convert model_id to OpenRouter format
    # If model_id doesn't have a provider prefix, check if it's OpenAI format
    # Otherwise, use as-is (for models like meta-llama/llama-3.1-8b-instruct)
    if "/" not in model_id:
        # Default to OpenAI format for backward compatibility
        openrouter_model = f"openai/{model_id}"
    else:
        # Already in OpenRouter format (e.g., "meta-llama/llama-3.1-8b-instruct")
        openrouter_model = model_id
    
    print(f"🌐 Using OpenRouter API - Model: {openrouter_model}")
    
    # CRITICAL: Explicitly prevent OpenAI fallback by temporarily removing OpenAI key
    # This is essential because ChatOpenAI may check environment variables during initialization
    original_openai_key = os.environ.get("OPENAI_API_KEY")
    original_openai_org = os.environ.get("OPENAI_ORGANIZATION")
    
    # Temporarily remove OpenAI keys to force OpenRouter
    # Keep them removed until model is created to prevent any fallback
    if original_openai_key:
        del os.environ["OPENAI_API_KEY"]
    if original_openai_org:
        del os.environ["OPENAI_ORGANIZATION"]
    
    try:
        # Create model with explicit OpenRouter configuration
        # IMPORTANT: Set openai_api_key explicitly to OpenRouter key
        # IMPORTANT: Set openai_api_base to OpenRouter endpoint
        # IMPORTANT: Set openai_organization to None to prevent OpenAI org usage
        # CRITICAL: Also set organization to None in default_headers to prevent OpenAI org header
        model = ChatOpenAI(
            model=openrouter_model,
            openai_api_key=openrouter_key,  # Use OpenRouter key explicitly
            openai_api_base="https://openrouter.ai/api/v1",  # Force OpenRouter endpoint
            openai_organization=None,  # Explicitly set to None to prevent OpenAI org usage
            temperature=properties["temperature"],
            max_retries=properties["max_retries"],
            timeout=properties["timeout"],
            request_timeout=120,  # Increase request timeout for long-running requests
            seed=42,  # Seed for reproducibility
            default_headers={
                "HTTP-Referer": "https://github.com/your-repo/MBTI-Regulator-Experiment",
                "X-Title": "MBTI Regulator Experiment",
                # Add headers to help with region restrictions
                "X-OpenRouter-Provider": "openai"
            }
        )
        
        # CRITICAL: Force client initialization by accessing it
        # This ensures the client is created with the correct configuration
        _ = model.client
        
        # CRITICAL: Verify the model is using OpenRouter IMMEDIATELY after creation
        # This must happen BEFORE environment variables are restored in finally block
        expected_base_url = "https://openrouter.ai/api/v1"
        actual_base_url = model.openai_api_base
        
        # CRITICAL: Check the underlying client's base_url and API key FIRST
        # This is the actual URL and key used for API calls
        if hasattr(model, 'client') and hasattr(model.client, '_client'):
            client_base_url = str(model.client._client.base_url).rstrip('/')
            actual_api_key = None
            
            # Get API key for verification
            if hasattr(model.client._client, 'api_key'):
                actual_api_key = str(model.client._client.api_key)
            
            # Debug output
            print(f"🔍 Model verification:")
            print(f"   openai_api_base: {actual_base_url}")
            print(f"   client._client.base_url: {client_base_url}")
            print(f"   client._client.api_key prefix: {actual_api_key[:20] if actual_api_key else 'N/A'}...")
            
            # Verify base_url
            if client_base_url != expected_base_url:
                raise ValueError(
                    f"❌ Model client is not using OpenRouter! "
                    f"Client Base URL: {client_base_url}, Expected: {expected_base_url}. "
                    f"Model openai_api_base attribute: {actual_base_url}"
                )
            
            # CRITICAL: Verify API key is OpenRouter key (not OpenAI key)
            if actual_api_key and not actual_api_key.startswith('sk-or-v1-'):
                # Try to fix it by recreating the client with correct configuration
                print(f"⚠️ Warning: Model using wrong API key ({actual_api_key[:20]}...), recreating client...")
                from openai import OpenAI
                model.client._client = OpenAI(
                    api_key=openrouter_key,
                    base_url="https://openrouter.ai/api/v1",
                    default_headers={
                        "HTTP-Referer": "https://github.com/your-repo/MBTI-Regulator-Experiment",
                        "X-Title": "MBTI Regulator Experiment"
                    }
                )
                # Re-verify after recreation
                actual_api_key_after = str(model.client._client.api_key)
                client_base_url_after = str(model.client._client.base_url).rstrip('/')
                if not actual_api_key_after.startswith('sk-or-v1-') or client_base_url_after != expected_base_url:
                    raise ValueError(
                        f"❌ Failed to recreate client with OpenRouter! "
                        f"API key prefix: {actual_api_key_after[:20]}..., "
                        f"Base URL: {client_base_url_after}"
                    )
                print(f"✅ Client recreated successfully with OpenRouter")
            
            # Explicitly set organization to None
            if hasattr(model.client._client, 'organization'):
                model.client._client.organization = None
            
            print(f"✅ Model verified: Using OpenRouter correctly")
        else:
            raise ValueError("❌ Model client structure is invalid! Cannot verify OpenRouter usage.")
        
        # Also verify openai_api_base attribute (should match)
        if actual_base_url != expected_base_url:
            raise ValueError(
                f"❌ Model is not using OpenRouter! "
                f"Base URL: {actual_base_url}, Expected: {expected_base_url}"
            )
        
        return model
    finally:
        # Restore original OpenAI keys if they existed
        # Note: We restore AFTER model creation to ensure model uses OpenRouter
        if original_openai_key:
            os.environ["OPENAI_API_KEY"] = original_openai_key
        if original_openai_org:
            os.environ["OPENAI_ORGANIZATION"] = original_openai_org
#!/usr/bin/env python3
"""
Diagnostic script to identify connection issues with Anthropic API
"""

import os
import sys
from dotenv import load_dotenv
import anthropic

print("=" * 60)
print("🔍 ANTHROPIC API CONNECTION DIAGNOSTICS")
print("=" * 60)

# Load environment variables
load_dotenv()

# Step 1: Check if API key exists
print("\n1️⃣ Checking API Key Configuration...")
api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("❌ ANTHROPIC_API_KEY is NOT set")
    print("\n🔧 FIX:")
    print("   1. Create a .env file in the project root")
    print("   2. Add: ANTHROPIC_API_KEY=your-api-key-here")
    print("   3. Or export it: export ANTHROPIC_API_KEY='your-api-key'")
    sys.exit(1)

print(f"✅ ANTHROPIC_API_KEY is set")
print(f"   Length: {len(api_key)} characters")
print(f"   Starts with: {api_key[:10]}...")

# Step 2: Check for common issues
print("\n2️⃣ Checking for Common Issues...")

issues_found = []

# Check for whitespace
if api_key != api_key.strip():
    issues_found.append("⚠️  API key has leading/trailing whitespace")
    print("⚠️  API key has leading/trailing whitespace")

# Check for quotes
if api_key.startswith('"') or api_key.startswith("'"):
    issues_found.append("⚠️  API key starts with quotes")
    print("⚠️  API key starts with quotes (should not have quotes)")

# Check for newlines
if '\n' in api_key or '\r' in api_key:
    issues_found.append("⚠️  API key contains newline characters")
    print("⚠️  API key contains newline characters")

# Check minimum length
if len(api_key) < 20:
    issues_found.append("⚠️  API key seems too short")
    print(f"⚠️  API key seems too short ({len(api_key)} chars)")

if not issues_found:
    print("✅ No obvious formatting issues detected")

# Step 3: Test network connectivity
print("\n3️⃣ Testing Network Connectivity...")
try:
    import socket
    socket.create_connection(("api.anthropic.com", 443), timeout=5)
    print("✅ Can reach api.anthropic.com:443")
except Exception as e:
    print(f"❌ Cannot reach api.anthropic.com:443")
    print(f"   Error: {e}")
    print("\n🔧 FIX:")
    print("   - Check your internet connection")
    print("   - Check if you're behind a firewall/proxy")
    print("   - Try: ping api.anthropic.com")
    sys.exit(1)

# Step 4: Test Anthropic client initialization
print("\n4️⃣ Testing Anthropic Client Initialization...")
try:
    # Clean the API key
    clean_key = api_key.strip().strip('"').strip("'")

    client = anthropic.Anthropic(api_key=clean_key)
    print("✅ Anthropic client initialized successfully")

    # Step 5: Test actual API call
    print("\n5️⃣ Testing API Call...")
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[{"role": "user", "content": "Hi"}]
    )
    print("✅ API call successful!")
    print(f"   Response: {response.content[0].text}")

except anthropic.AuthenticationError as e:
    print("❌ Authentication failed - API key is invalid")
    print(f"   Error: {e}")
    print("\n🔧 FIX:")
    print("   - Check your API key at https://console.anthropic.com/")
    print("   - Make sure it's copied correctly without extra characters")
    sys.exit(1)

except anthropic.APIConnectionError as e:
    print("❌ Connection error - Cannot reach Anthropic API")
    print(f"   Error: {e}")

    if issues_found:
        print("\n🔧 LIKELY CAUSES:")
        for issue in issues_found:
            print(f"   {issue}")
        print("\n🔧 FIX:")
        print("   1. Clean your API key in .env:")
        print(f"      Before: ANTHROPIC_API_KEY={repr(api_key)}")
        print(f"      After:  ANTHROPIC_API_KEY={clean_key}")
    else:
        print("\n🔧 POSSIBLE CAUSES:")
        print("   - Network/firewall issue")
        print("   - DNS resolution problem")
        print("   - Proxy configuration needed")
    sys.exit(1)

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL CHECKS PASSED - Your setup is working!")
print("=" * 60)
